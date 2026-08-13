#!/usr/bin/env python3
"""
replay.py

EOS Replay Engine

Reads binary tick records produced by EventStore
and republishes them through the decoder.
"""

from __future__ import annotations

import argparse
import struct
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from decoder import decode_tick
from envelope import EventEnvelope
from event_bus import EventBus


class Replay:

    def __init__(
        self,
        filename: str | Path,
        decoder: Callable[[bytes], Any] = decode_tick,
    ):
        self.filename = Path(filename)
        self.decoder = decoder

    def envelopes(self):
        """Yield raw framed records as envelopes in their recorded order."""
        packets = 0

        with self.filename.open("rb") as f:

            while True:

                header = f.read(4)

                if not header:
                    break

                if len(header) != 4:
                    raise ValueError(f"Truncated frame header after {packets} packets")

                size = struct.unpack("<I", header)[0]

                payload = f.read(size)
                if len(payload) != size:
                    raise ValueError(f"Truncated payload for packet {packets + 1}")

                event = self.decoder(payload)
                packets += 1

                exchange_time_ms = getattr(getattr(event, "meta", None), "exchange_time_ms", 0)
                received_at = datetime.fromtimestamp(exchange_time_ms / 1_000, tz=UTC)
                yield EventEnvelope(
                    event=event,
                    payload=payload,
                    received_at=received_at,
                    size=size,
                )

    async def publish(self, bus: EventBus) -> int:
        """Republish stored records into the live event pipeline."""
        packets = 0
        for envelope in self.envelopes():
            await bus.publish(envelope)
            packets += 1
        return packets

    def replay(self) -> int:
        """Print a human-readable replay without constructing a live bus."""
        packets = 0
        for envelope in self.envelopes():
            event = envelope.event
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
        return packets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay an EOS raw tick log")
    parser.add_argument("filename", type=Path, help="Path to a framed tick.bin file")
    arguments = parser.parse_args()
    Replay(arguments.filename).replay()
