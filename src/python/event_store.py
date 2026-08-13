"""
event_store.py

EOS Binary Event Store
"""

from __future__ import annotations

import json
import struct
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from envelope import EventEnvelope
from models import AlphaEstimate, EconomicsEvaluated, ForwardOutcomeRealized, MicrostructureEstimated


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


class DerivedEventStore:
    """Append versioned derived events without modifying raw evidence."""

    def __init__(self, root="storage/derived"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def on_microstructure(self, estimate: MicrostructureEstimated) -> None:
        """Persist a JSONL research record partitioned by symbol and UTC day."""
        day = datetime.fromtimestamp(
            estimate.meta.exchange_time_ms / 1_000,
            tz=UTC,
        ).strftime("%Y-%m-%d")
        folder = self.root / "microstructure" / estimate.meta.symbol / day
        folder.mkdir(parents=True, exist_ok=True)

        record = asdict(estimate)
        with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, separators=(",", ":"), sort_keys=True))
            stream.write("\n")

    def on_economics(self, evaluation: EconomicsEvaluated) -> None:
        self._append("economics", evaluation)

    def on_alpha(self, estimate: AlphaEstimate) -> None:
        self._append("alpha", estimate)

    def on_forward_outcome(self, outcome: ForwardOutcomeRealized) -> None:
        self._append("forward_outcomes", outcome)

    def _append(self, category: str, event) -> None:
        day = datetime.fromtimestamp(
            event.meta.exchange_time_ms / 1_000,
            tz=UTC,
        ).strftime("%Y-%m-%d")
        folder = self.root / category / event.meta.symbol / day
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(event), separators=(",", ":"), sort_keys=True))
            stream.write("\n")
