import unittest

from engines.alpha_estimator import AlphaEstimator
from engines.economic.config import EconomicConfig
from models import EventMetadata, MicrostructureEstimated


def micro() -> MicrostructureEstimated:
    return MicrostructureEstimated(
        EventMetadata("micro-1", 0, 1, 1, 0, 1_000, 1_000, 1, "test", "", "EURUSD", "tick-1", "", "", "", 0),
        1.0, 2.0, None, None, None, 0.0, 0.0,
    )


class AlphaEstimatorTests(unittest.TestCase):
    def test_disabled_prototype_emits_an_explicit_unavailable_event(self):
        result = AlphaEstimator(config=EconomicConfig()).estimate(micro())

        self.assertEqual(result.outcome, "UNAVAILABLE")
        self.assertEqual(result.reason, "PROTOTYPE_EDGE_DISABLED")
        self.assertEqual(result.meta.parent_id_1, "micro-1")
        self.assertIsNone(result.expected_edge_bps)
