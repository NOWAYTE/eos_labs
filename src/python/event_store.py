"""
event_store.py

EOS Binary Event Store
"""

from __future__ import annotations

import struct
from pathlib import Path

from envelope import EventEnvelope


class EventStore:

    def __init__(self, root="storage"):

        self.root = Path(root)

        self.root.mkdir(parents=True, exist_ok=True)

    def on_tick(self, envelope: EventEnvelope):

        event = envelope.event

        #
        # storage/EURUSD/2026-07-30/
        #

        day = envelope.received_at.strftime("%Y-%m-%d")

        folder = self.root / event.meta.symbol / day

        folder.mkdir(parents=True, exist_ok=True)

        file = folder / "tick.bin"

        with file.open("ab") as f:

            #
            # packet size
            #

            f.write(struct.pack("<I", envelope.size))

            #
            # original MT5 payload
            #

            f.write(envelope.payload)
