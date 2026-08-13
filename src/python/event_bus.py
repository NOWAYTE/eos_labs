"""
event_bus.py

EOS In-Process Event Bus
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Type

from envelope import EventEnvelope


logger = logging.getLogger(__name__)


class BackpressurePolicy(str, Enum):
    """The explicit behavior when a subscriber queue is full."""

    BLOCK = "block"
    DROP_NEWEST = "drop_newest"


@dataclass(slots=True)
class Subscription:
    event_type: Type
    handler: Callable
    receive_envelope: bool
    queue: asyncio.Queue[EventEnvelope]
    backpressure: BackpressurePolicy
    task: asyncio.Task | None = None
    received: int = 0
    processed: int = 0
    dropped: int = 0
    failures: int = 0


class EventBus:
    """
    EOS event router.

    Publishers always send :class:`EventEnvelope` objects.

    Subscribers can receive either:

    - EventEnvelope
    - decoded domain events

    depending on their handler type. Publishing only admits an event to the
    bounded ingestion queue; subscriber work happens on independent workers.

    A ``BLOCK`` subscription preserves its events by applying explicit
    backpressure. ``DROP_NEWEST`` is intended only for derived, disposable
    work and records every dropped event in the subscription metrics.
    """

    def __init__(self, ingestion_queue_size: int = 10_000):
        self._handlers = defaultdict(list)
        self._ingestion_queue: asyncio.Queue[EventEnvelope] = asyncio.Queue(
            maxsize=ingestion_queue_size
        )
        self._dispatcher_task: asyncio.Task | None = None
        self._started = False
        self.published = 0

    def subscribe(
        self,
        event_type: Type,
        handler: Callable,
        receive_envelope: bool = False,
        *,
        queue_size: int = 1_000,
        backpressure: BackpressurePolicy = BackpressurePolicy.BLOCK,
    ) -> Subscription:
        """Register a worker before :meth:`start` is called."""
        if self._started:
            raise RuntimeError("Subscribe before starting the EventBus")
        if queue_size <= 0:
            raise ValueError("queue_size must be greater than zero")

        subscription = Subscription(
            event_type=event_type,
            handler=handler,
            receive_envelope=receive_envelope,
            queue=asyncio.Queue(maxsize=queue_size),
            backpressure=backpressure,
        )
        self._handlers[event_type].append(subscription)
        return subscription

    async def start(self) -> None:
        """Start dispatcher and subscriber workers."""
        if self._started:
            return

        self._started = True
        for subscriptions in self._handlers.values():
            for subscription in subscriptions:
                subscription.task = asyncio.create_task(
                    self._run_subscription(subscription),
                    name=f"event-bus:{subscription.event_type.__name__}",
                )
        self._dispatcher_task = asyncio.create_task(
            self._dispatch(), name="event-bus:dispatcher"
        )

    async def publish(
        self,
        envelope: EventEnvelope,
    ) -> None:
        """Admit an event, applying upstream backpressure only when full."""
        if not self._started:
            raise RuntimeError("Start the EventBus before publishing")
        await self._ingestion_queue.put(envelope)
        self.published += 1

    def publish_nowait(self, envelope: EventEnvelope) -> None:
        """Try immediate admission; callers handle :class:`QueueFull` explicitly."""
        if not self._started:
            raise RuntimeError("Start the EventBus before publishing")
        self._ingestion_queue.put_nowait(envelope)
        self.published += 1

    def metrics(self) -> dict:
        """A snapshot suitable for live health reporting and manifests."""
        return {
            "published": self.published,
            "ingestion_queue_depth": self._ingestion_queue.qsize(),
            "subscriptions": [
                {
                    "event_type": item.event_type.__name__,
                    "queue_depth": item.queue.qsize(),
                    "received": item.received,
                    "processed": item.processed,
                    "dropped": item.dropped,
                    "failures": item.failures,
                }
                for group in self._handlers.values()
                for item in group
            ],
        }

    async def join(self) -> None:
        """Wait until all events admitted so far have reached every worker."""
        await self._ingestion_queue.join()
        await asyncio.gather(
            *(subscription.queue.join()
              for subscriptions in self._handlers.values()
              for subscription in subscriptions)
        )

    async def stop(self) -> None:
        """Cancel workers. Call after closing ingress during service shutdown."""
        tasks = [
            task
            for task in [
                self._dispatcher_task,
                *(subscription.task
                  for subscriptions in self._handlers.values()
                  for subscription in subscriptions),
            ]
            if task is not None
        ]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._dispatcher_task = None
        for subscriptions in self._handlers.values():
            for subscription in subscriptions:
                subscription.task = None
        self._started = False

    async def _dispatch(self) -> None:
        while True:
            envelope = await self._ingestion_queue.get()
            try:
                for subscription in self._handlers.get(type(envelope.event), []):
                    await self._enqueue(subscription, envelope)
            finally:
                self._ingestion_queue.task_done()

    async def _enqueue(
        self,
        subscription: Subscription,
        envelope: EventEnvelope,
    ) -> None:
        if subscription.backpressure is BackpressurePolicy.BLOCK:
            await subscription.queue.put(envelope)
            subscription.received += 1
            return

        try:
            subscription.queue.put_nowait(envelope)
            subscription.received += 1
        except asyncio.QueueFull:
            subscription.dropped += 1
            logger.warning(
                "EventBus dropped %s for %s because its queue is full",
                type(envelope.event).__name__,
                getattr(subscription.handler, "__qualname__", repr(subscription.handler)),
            )

    async def _run_subscription(self, subscription: Subscription) -> None:
        while True:
            envelope = await subscription.queue.get()
            try:
                argument: Any = envelope if subscription.receive_envelope else envelope.event
                if inspect.iscoroutinefunction(subscription.handler) or inspect.iscoroutinefunction(
                    getattr(subscription.handler, "__call__", None)
                ):
                    await subscription.handler(argument)
                else:
                    # Existing handlers are synchronous (for example EventStore).
                    # Run them off the event loop so they cannot pause TCP ingestion.
                    await asyncio.to_thread(subscription.handler, argument)
                subscription.processed += 1
            except Exception:
                subscription.failures += 1
                logger.exception(
                    "EventBus handler failed: %s",
                    getattr(subscription.handler, "__qualname__", repr(subscription.handler)),
                )
            finally:
                subscription.queue.task_done()

    def clear(self):
        if self._started:
            raise RuntimeError("Stop the EventBus before clearing subscriptions")
        self._handlers.clear()
    def subscriber_count(
        self,
        event_type: Type,
    ):

        return len(self._handlers.get(event_type, []))
