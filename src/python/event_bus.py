"""
event_bus.py

EOS In-Process Event Bus
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Type

from envelope import EventEnvelope


class EventBus:
    """
    EOS event router.

    Publishers always send EventEnvelope.

    Subscribers can receive either:

    - EventEnvelope
    - decoded domain events

    depending on their handler type.
    """


    def __init__(self):

        self._handlers = defaultdict(list)


    def subscribe(
        self,
        event_type: Type,
        handler: Callable,
        receive_envelope: bool = False,
    ):

        self._handlers[event_type].append(
            (
                handler,
                receive_envelope
            )
        )


    def publish(
        self,
        envelope: EventEnvelope,
    ):

        event = envelope.event

        event_cls = type(event)

        handlers = self._handlers.get(
            event_cls,
            []
        )

        for handler, receive_envelope in handlers:

            if receive_envelope:
                handler(envelope)

            else:
                handler(event)


    def clear(self):

        self._handlers.clear()


    def subscriber_count(
        self,
        event_type: Type,
    ):

        return len(
            self._handlers.get(
                event_type,
                []
            )
        )
