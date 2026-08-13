import unittest

from engines.microstructure_estimator import MicrostructureEstimator
from envelope import EventEnvelope
from event_bus import EventBus
from models import EventMetadata, MicrostructureEstimated, TickObserved


def tick(sequence: int, timestamp_ms: int, bid: float, ask: float) -> TickObserved:
    return TickObserved(
        meta=EventMetadata(
            event_id=f"tick-{sequence}", event_type=0, domain=0,
            schema_major=1, schema_minor=0,
            exchange_time_ms=timestamp_ms, local_time_ms=timestamp_ms,
            monotonic_counter=sequence, producer="test", session_id="session",
            symbol="EURUSD", parent_id_1="", parent_id_2="",
            algorithm="", algorithm_version="", checksum=0,
        ),
        bid=bid, ask=ask, last=0.0, volume_real=0.0,
        volume_tick=0, flags=0,
    )


class MicrostructureEstimatorTests(unittest.TestCase):
    def test_calculates_level_one_metrics_and_lineage(self):
        estimator = MicrostructureEstimator(window_size=2)
        estimator.estimate(tick(1, 1_000, 100, 102))
        estimate = estimator.estimate(tick(2, 2_000, 102, 104))

        self.assertAlmostEqual(estimate.spread_bps, 194.174757, places=6)
        self.assertEqual(estimate.tick_to_vol_ratio, 1.0)
        self.assertEqual(estimate.meta.parent_id_1, "tick-2")
        self.assertEqual(estimate.meta.event_id, "micro:tick-2:1.0.0")
        self.assertEqual(estimate.meta.algorithm, "Level1Descriptive")

    def test_unobservable_level_two_values_remain_unavailable(self):
        estimate = MicrostructureEstimator().estimate(tick(1, 1_000, 100, 102))

        self.assertIsNone(estimate.tick_to_vol_ratio)
        self.assertIsNone(estimate.book_imbalance)
        self.assertIsNone(estimate.toxicity_score)
        self.assertIsNone(estimate.queue_position_est)
        self.assertEqual(estimate.confidence_overall, 0.0)
        self.assertEqual(estimate.confidence_queue, 0.0)


class MicrostructureBusTests(unittest.IsolatedAsyncioTestCase):
    async def test_estimate_is_published_as_a_derived_event(self):
        bus = EventBus()
        received = []
        estimator = MicrostructureEstimator(bus=bus)
        bus.subscribe(TickObserved, estimator.on_tick)
        bus.subscribe(MicrostructureEstimated, received.append)
        await bus.start()
        try:
            await bus.publish(
                EventEnvelope(
                    event=tick(1, 1_000, 100, 102),
                    payload=b"",
                    received_at=None,
                    size=0,
                )
            )
            await bus.join()
        finally:
            await bus.stop()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].meta.parent_id_1, "tick-1")
