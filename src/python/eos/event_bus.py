"""
event_bus.py

Simple publish/subscribe event bus.
"""

from typing import Callable, List, Any


class EventBus:
    def __init__(self):
        self._subscribers: List[Callable[[Any], None]] = []

    def subscribe(self, callback: Callable[[Any], None]) -> None:
        self._subscribers.append(callback)

    def publish(self, event: Any) -> None:
        for callback in self._subscribers:
            callback(event)
