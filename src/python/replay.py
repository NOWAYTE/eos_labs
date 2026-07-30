#!/usr/bin/env python3
"""
replay.py

EOS Replay Engine

Reads binary tick records produced by EventStore
and republishes them through the decoder.
"""

from __future__ import annotations

import struct
from pathlib import Path

from decoder import decode_tick


class Replay:

    def __init__(self, filename: str):

        self.filename = Path(filename)

    def replay(self):

        packets = 0

        with self.filename.open("rb") as f:

            while True:

                header = f.read(4)

                if not header:
                    break

                size = struct.unpack("<I", header)[0]

                payload = f.read(size)

                event = decode_tick(payload)

                packets += 1

                print(
                    f"[{packets:06d}] "
                    f"{event.meta.event_id} "
                    f"{event.meta.symbol} "
                    f"Bid={event.bid:.5f} "
                    f"Ask={event.ask:.5f}"
                )

        print()
        print(f"Replay complete ({packets} packets).")


if __name__ == "__main__":

    Replay(
        "storage/EURUSD/2026-07-30/tick.bin"
    ).replay()
