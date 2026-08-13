import math
import unittest
from datetime import UTC, datetime

from engines.market_state_engine import MarketStateEngine
from models import EventMetadata, TickObserved


def tick(*, event_id: str, timestamp_ms: int, bid: float, ask: float) -> TickObserved:
    return TickObserved(
        meta=EventMetadata(
            event_id=event_id,
            event_type=0,
            domain=0,
            schema_major=1,
            schema_minor=0,
            exchange_time_ms=timestamp_ms,
            local_time_ms=timestamp_ms,
            monotonic_counter=int(event_id),
            producer="test",
            session_id="session",
            symbol="EURUSD",
            parent_id_1="",
            parent_id_2="",
            algorithm="",
            algorithm_version="",
            checksum=0,
        ),
        bid=bid,
        ask=ask,
        last=0.0,
        volume_real=0.0,
        volume_tick=0,
        flags=0,
    )


class MarketStateEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = MarketStateEngine(window_size=2)

    def test_uses_exchange_time_and_calculates_window_metrics(self):
        self.engine.on_tick(tick(event_id="1", timestamp_ms=1_000, bid=100, ask=102))
        self.engine.on_tick(tick(event_id="2", timestamp_ms=2_000, bid=102, ask=106))
        state = self.engine.on_tick(tick(event_id="3", timestamp_ms=4_000, bid=104, ask=106))

        self.assertEqual(state.tick_count, 3)
        self.assertEqual(state.latest_bid, 104)
        self.assertEqual(state.latest_ask, 106)
        self.assertEqual(state.latest_mid, 105)
        self.assertEqual(state.current_spread, 2)
        self.assertEqual(state.average_spread, 3)
        self.assertTrue(math.isclose(state.rolling_volatility, 0.5))
        self.assertEqual(state.ticks_per_second, 0.5)
        self.assertEqual(state.last_update, datetime.fromtimestamp(4, tz=UTC))

    def test_same_ticks_produce_the_same_state(self):
        ticks = [
            tick(event_id="1", timestamp_ms=1_000, bid=1.10, ask=1.12),
            tick(event_id="2", timestamp_ms=1_500, bid=1.11, ask=1.14),
            tick(event_id="3", timestamp_ms=2_500, bid=1.12, ask=1.16),
        ]
        replay_engine = MarketStateEngine(window_size=2)

        for observed in ticks:
            self.engine.on_tick(observed)
            replay_engine.on_tick(observed)

        self.assertEqual(self.engine.get("EURUSD"), replay_engine.get("EURUSD"))

    def test_non_positive_time_window_has_zero_tick_rate(self):
        self.engine.on_tick(tick(event_id="1", timestamp_ms=2_000, bid=1.10, ask=1.11))
        state = self.engine.on_tick(
            tick(event_id="2", timestamp_ms=1_000, bid=1.11, ask=1.12)
        )

        self.assertEqual(state.ticks_per_second, 0.0)
