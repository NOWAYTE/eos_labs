import unittest

from engines.economic.config import EconomicConfig
from engines.economic.edge_model import EdgeEstimate
from engines.economic.engine import EconomicEngine
from models import AlphaEstimate, EventMetadata, MicrostructureEstimated


class FixedEdgeModel:
    def __init__(self, edge: EdgeEstimate | None):
        self.edge = edge

    def estimate(self, _microstructure):
        return self.edge


def microstructure() -> MicrostructureEstimated:
    return MicrostructureEstimated(
        meta=EventMetadata(
            event_id="micro:tick-1:1.0.0", event_type=0, domain=1,
            schema_major=1, schema_minor=0, exchange_time_ms=1_000,
            local_time_ms=1_000, monotonic_counter=1, producer="test",
            session_id="session", symbol="EURUSD", parent_id_1="tick-1",
            parent_id_2="", algorithm="test", algorithm_version="1", checksum=0,
        ),
        tick_to_vol_ratio=1.0, spread_bps=2.0, book_imbalance=None,
        toxicity_score=None, queue_position_est=None,
        confidence_overall=0.0, confidence_queue=0.0,
    )


class EconomicEngineTests(unittest.TestCase):
    def setUp(self):
        self.config = EconomicConfig(
            slippage_cost_bps=0.5, fee_cost_bps=0.25, cost_uncertainty_bps=0.5,
        )

    def test_calculates_auditable_economic_approval(self):
        engine = EconomicEngine(
            config=self.config,
            edge_model=FixedEdgeModel(EdgeEstimate(6.0, 1.0, 500, 1, "test", "1")),
        )
        result = engine.evaluate(microstructure())

        self.assertEqual(result.outcome, "APPROVED")
        self.assertAlmostEqual(result.expected_cost_bps, 1.75)
        self.assertAlmostEqual(result.nev_bps, 1.75)
        self.assertGreater(result.ppe, 0.99)
        self.assertAlmostEqual(result.execution_budget_bps, 4.5)
        self.assertEqual(result.meta.parent_id_1, "micro:tick-1:1.0.0")

    def test_default_configuration_is_versioned_and_safe_by_default(self):
        config = EconomicConfig.from_file()
        result = EconomicEngine(config=config).evaluate(microstructure())

        self.assertEqual(config.model_version, "EconomicModelV1")
        self.assertFalse(config.prototype_edge_enabled)
        self.assertEqual(result.reason, "MISSING_EDGE_ESTIMATE")

    def test_missing_edge_is_an_explicit_rejection(self):
        result = EconomicEngine(
            config=self.config, edge_model=FixedEdgeModel(None)
        ).evaluate(microstructure())

        self.assertEqual(result.outcome, "REJECTED")
        self.assertEqual(result.reason, "MISSING_EDGE_ESTIMATE")
        self.assertIsNone(result.nev_bps)

    def test_consumes_an_alpha_event_with_matching_lineage(self):
        alpha = AlphaEstimate(
            EventMetadata("alpha-1", 0, 1, 1, 0, 1_000, 1_000, 1, "alpha", "session", "EURUSD", "micro:tick-1:1.0.0", "", "test", "1", 0),
            6.0, 1.0, 500, 1, 0.0, "AVAILABLE", "test",
        )
        result = EconomicEngine(config=self.config).evaluate(microstructure(), alpha)

        self.assertEqual(result.outcome, "APPROVED")
        self.assertEqual(result.meta.parent_id_1, "micro:tick-1:1.0.0")

    def test_gate_rejects_when_positive_value_has_insufficient_probability(self):
        engine = EconomicEngine(
            config=self.config,
            edge_model=FixedEdgeModel(EdgeEstimate(5.0, 10.0, 500, 1, "test", "1")),
        )
        result = engine.evaluate(microstructure())

        self.assertEqual(result.outcome, "REJECTED")
        self.assertEqual(result.reason, "ECONOMIC_GATE_FAILED")
