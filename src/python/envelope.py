"""
envelope.py

EOS Event Envelope

Carries both the decoded event and the original binary payload
through the event pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class EventEnvelope:
    """
    Canonical event container.

    Attributes
    ----------
    event
        Decoded Python event object (TickObserved, BarClosed, etc.)

    payload
        Original binary payload exactly as received from MT5.

    received_at
        UTC timestamp when the gateway received the packet.

    size
        Payload size in bytes.
    """

    event: Any

    payload: bytes

    received_at: datetime

    size: int
