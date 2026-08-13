"""Deterministic Level-1 microstructure interpretation.

This initial estimator exposes only quantities supportable by tick data. It
does not claim to observe an order book, queue position, or informed flow.
"""

from __future__ import annotations

from datetime import UTC, datetime

from envelope import EventEnvelope
from event_bus import EventBus
from models import EventMetadata, MicrostructureEstimated, TickObserved

from .market_state_engine import MarketStateEngine


class MicrostructureEstimator:
    """Publish a lineage-linked Level-1 interpretation for every tick."""

    PRODUCER = "MicrostructureEstimator"
    ALGORITHM = "Level1Descriptive"
    ALGORITHM_VERSION = "1.0.0"

    def __init__(self, bus: EventBus | None = None, window_size: int = 100):
        self.bus = bus
        self.market_state = MarketStateEngine(window_size=window_size)

    def estimate(self, tick: TickObserved) -> MicrostructureEstimated:
        """Create a deterministic estimate from a tick in event order."""
        state = self.market_state.on_tick(tick)
        spread_bps = (
            (state.current_spread / state.latest_mid) * 10_000
            if state.latest_mid > 0
            else None
        )
        tick_to_vol_ratio = (
            state.ticks_per_second / state.rolling_volatility
            if state.rolling_volatility > 0
            else None
        )

        return MicrostructureEstimated(
            meta=EventMetadata(
                event_id=(
                    f"micro:{tick.meta.event_id}:{self.ALGORITHM_VERSION}"
                ),
                event_type=0,
                domain=1,
                schema_major=1,
                schema_minor=0,
                exchange_time_ms=tick.meta.exchange_time_ms,
                local_time_ms=tick.meta.local_time_ms,
                monotonic_counter=tick.meta.monotonic_counter,
                producer=self.PRODUCER,
                session_id=tick.meta.session_id,
                symbol=tick.meta.symbol,
                parent_id_1=tick.meta.event_id,
                parent_id_2="",
                algorithm=self.ALGORITHM,
                algorithm_version=self.ALGORITHM_VERSION,
                checksum=0,
            ),
            tick_to_vol_ratio=tick_to_vol_ratio,
            spread_bps=spread_bps,
            book_imbalance=None,
            toxicity_score=None,
            queue_position_est=None,
            confidence_overall=0.0,
            confidence_queue=0.0,
        )

    async def on_tick(self, tick: TickObserved) -> MicrostructureEstimated:
        """Estimate and publish a derived event when connected to an EventBus."""
        estimate = self.estimate(tick)
        if self.bus is not None:
            received_at = datetime.fromtimestamp(
                tick.meta.exchange_time_ms / 1_000,
                tz=UTC,
            )
            await self.bus.publish(
                EventEnvelope(
                    event=estimate,
                    payload=b"",
                    received_at=received_at,
                    size=0,
                )
            )
        return estimate
