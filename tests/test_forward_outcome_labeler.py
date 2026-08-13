import unittest

from engines.forward_outcome_labeler import ForwardOutcomeLabeler
from models import AlphaEstimate, EventMetadata, MicrostructureEstimated, TickObserved


def metadata(event_id, timestamp, parent=""):
    return EventMetadata(event_id, 0, 1, 1, 0, timestamp, timestamp, timestamp, "test", "", "EURUSD", parent, "", "", "", 0)


def tick(event_id, timestamp, bid, ask):
    return TickObserved(metadata(event_id, timestamp), bid, ask, 0, 0, 0, 0)


class ForwardOutcomeLabelerTests(unittest.IsolatedAsyncioTestCase):
    async def test_labels_directional_return_at_the_first_tick_after_horizon(self):
        labeler = ForwardOutcomeLabeler()
        await labeler.on_tick(tick("tick-1", 1_000, 100, 102))
        await labeler.on_microstructure(
            MicrostructureEstimated(metadata("micro-1", 1_000, "tick-1"), 1, 2, None, None, None, 0, 0)
        )
        await labeler.on_alpha(
            AlphaEstimate(metadata("alpha-1", 1_000, "micro-1"), 1, 1, 500, 1, 0, "AVAILABLE", "test")
        )
        captured = []

        async def capture(outcome):
            captured.append(outcome)

        labeler._publish = capture
        await labeler.on_tick(tick("tick-before", 1_400, 102, 104))
        await labeler.on_tick(tick("tick-after", 1_600, 104, 106))

        self.assertEqual(len(captured), 1)
        self.assertAlmostEqual(captured[0].realized_return_bps, 396.03960396)
        self.assertEqual(captured[0].meta.parent_id_1, "alpha-1")

    async def test_retention_discards_old_tick_history(self):
        labeler = ForwardOutcomeLabeler(retention_ms=500)
        await labeler.on_tick(tick("old", 1_000, 100, 102))
        await labeler.on_tick(tick("new", 2_000, 102, 104))

        self.assertNotIn("old", labeler._ticks)
        self.assertIn("new", labeler._ticks)
