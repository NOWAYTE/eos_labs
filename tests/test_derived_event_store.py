import json
import tempfile
import unittest
from pathlib import Path

from event_store import DerivedEventStore
from models import EventMetadata, MicrostructureEstimated


def estimate() -> MicrostructureEstimated:
    return MicrostructureEstimated(
        meta=EventMetadata(
            event_id="micro:tick-1:1.0.0", event_type=0, domain=1,
            schema_major=1, schema_minor=0,
            exchange_time_ms=1_725_134_400_000,
            local_time_ms=1_725_134_400_000, monotonic_counter=1,
            producer="MicrostructureEstimator", session_id="session",
            symbol="EURUSD", parent_id_1="tick-1", parent_id_2="",
            algorithm="Level1Descriptive", algorithm_version="1.0.0", checksum=0,
        ),
        tick_to_vol_ratio=2.0, spread_bps=1.5, book_imbalance=None,
        toxicity_score=None, queue_position_est=None,
        confidence_overall=0.0, confidence_queue=0.0,
    )


class DerivedEventStoreTests(unittest.TestCase):
    def test_writes_derived_events_separately_as_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            store = DerivedEventStore(directory)
            store.on_microstructure(estimate())

            files = list(Path(directory).rglob("events.jsonl"))
            self.assertEqual(len(files), 1)
            record = json.loads(files[0].read_text(encoding="utf-8"))

        self.assertEqual(record["meta"]["parent_id_1"], "tick-1")
        self.assertEqual(record["spread_bps"], 1.5)
        self.assertIsNone(record["queue_position_est"])
