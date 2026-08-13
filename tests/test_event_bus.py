import asyncio
import time
import unittest

from event_bus import BackpressurePolicy, EventBus
from envelope import EventEnvelope


class Tick:
    def __init__(self, sequence: int):
        self.sequence = sequence


def envelope(sequence: int) -> EventEnvelope:
    return EventEnvelope(
        event=Tick(sequence),
        payload=b"tick",
        received_at=None,
        size=4,
    )


class EventBusTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bus = EventBus(ingestion_queue_size=16)

    async def asyncTearDown(self):
        await self.bus.stop()

    async def test_slow_sync_subscriber_does_not_block_other_subscribers(self):
        received = asyncio.Event()

        def slow_handler(_event):
            time.sleep(0.1)

        async def fast_handler(_event):
            received.set()

        self.bus.subscribe(Tick, slow_handler)
        self.bus.subscribe(Tick, fast_handler)
        await self.bus.start()
        await self.bus.publish(envelope(1))

        await asyncio.wait_for(received.wait(), timeout=0.25)

    async def test_handler_failure_is_isolated(self):
        received = []

        def failing_handler(_event):
            raise RuntimeError("expected test failure")

        def healthy_handler(event):
            received.append(event.sequence)

        self.bus.subscribe(Tick, failing_handler)
        self.bus.subscribe(Tick, healthy_handler)
        await self.bus.start()
        await self.bus.publish(envelope(1))

        await self.bus.join()
        self.assertEqual(received, [1])

    async def test_subscriber_queue_preserves_order(self):
        received = []

        def handler(event):
            received.append(event.sequence)

        self.bus.subscribe(Tick, handler)
        await self.bus.start()
        for sequence in range(5):
            await self.bus.publish(envelope(sequence))

        await self.bus.join()
        self.assertEqual(received, [0, 1, 2, 3, 4])

    async def test_drop_newest_is_accounted_for(self):
        blocker = asyncio.Event()

        async def slow_handler(_event):
            await blocker.wait()

        subscription = self.bus.subscribe(
            Tick,
            slow_handler,
            queue_size=1,
            backpressure=BackpressurePolicy.DROP_NEWEST,
        )
        await self.bus.start()
        for sequence in range(4):
            await self.bus.publish(envelope(sequence))

        await asyncio.sleep(0.01)
        self.assertGreater(subscription.dropped, 0)
        blocker.set()

    async def test_metrics_reports_queue_and_worker_counters(self):
        self.bus.subscribe(Tick, lambda _event: None)
        await self.bus.start()
        await self.bus.publish(envelope(1))
        await self.bus.join()

        metrics = self.bus.metrics()
        self.assertEqual(metrics["published"], 1)
        self.assertEqual(metrics["ingestion_queue_depth"], 0)
        self.assertEqual(metrics["subscriptions"][0]["processed"], 1)
