import tempfile
import unittest
from pathlib import Path

from experiment_runner import run


class ExperimentRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_replay_writes_manifest_and_all_derived_layers(self):
        root = Path(__file__).parents[1]
        source = root / "storage" / "EURUSD" / "2026-08-13" / "tick.bin"
        config = root / "config" / "economic_engine.prototype.json"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "experiment"
            manifest = await run(source, config, output)

            self.assertEqual(manifest["raw_events"], 65)
            self.assertTrue((output / "manifest.json").exists())
            self.assertEqual(
                next(item for item in manifest["subscriptions"] if item["event_type"] == "MicrostructureEstimated")["processed"],
                65,
            )
            self.assertTrue(list((output / "derived" / "microstructure").rglob("events.jsonl")))
            self.assertTrue(list((output / "derived" / "alpha").rglob("events.jsonl")))
            self.assertTrue(list((output / "derived" / "economics").rglob("events.jsonl")))
