from __future__ import annotations

from datetime import UTC, datetime

from engines.economic.config import EconomicConfig
from engines.economic.edge_model import PrototypeEdgeModelV0
from envelope import EventEnvelope
from event_bus import EventBus
from models import AlphaEstimate, EventMetadata, MicrostructureEstimated


class AlphaEstimator:
    """Publish a declared prototype alpha result for every microstructure event."""

    def __init__(self, bus: EventBus | None = None, config: EconomicConfig | None = None):
        self.bus = bus
        self.config = config or EconomicConfig.from_file()
        self.model = PrototypeEdgeModelV0(
            enabled=self.config.prototype_edge_enabled,
            expected_edge_bps=self.config.prototype_expected_edge_bps,
            edge_uncertainty_bps=self.config.prototype_edge_uncertainty_bps,
            horizon_ms=self.config.prototype_horizon_ms,
            direction=self.config.prototype_direction,
        )

    def estimate(self, micro: MicrostructureEstimated) -> AlphaEstimate:
        edge = self.model.estimate(micro)
        available = edge is not None
        return AlphaEstimate(
            meta=EventMetadata(
                event_id=f"alpha:{micro.meta.event_id}:PrototypeEdgeModelV0",
                event_type=0, domain=1, schema_major=1, schema_minor=0,
                exchange_time_ms=micro.meta.exchange_time_ms,
                local_time_ms=micro.meta.local_time_ms,
                monotonic_counter=micro.meta.monotonic_counter,
                producer="AlphaEstimator", session_id=micro.meta.session_id,
                symbol=micro.meta.symbol, parent_id_1=micro.meta.event_id,
                parent_id_2="", algorithm="PrototypeEdgeModel",
                algorithm_version="0.0.0", checksum=0,
            ),
            expected_edge_bps=edge.expected_edge_bps if edge else None,
            edge_uncertainty_bps=edge.edge_uncertainty_bps if edge else None,
            horizon_ms=edge.horizon_ms if edge else None,
            direction=edge.direction if edge else None,
            confidence=0.0,
            outcome="AVAILABLE" if available else "UNAVAILABLE",
            reason="PROTOTYPE_EDGE" if available else "PROTOTYPE_EDGE_DISABLED",
        )

    async def on_microstructure(self, micro: MicrostructureEstimated) -> AlphaEstimate:
        alpha = self.estimate(micro)
        if self.bus:
            received_at = datetime.fromtimestamp(micro.meta.exchange_time_ms / 1_000, tz=UTC)
            await self.bus.publish(EventEnvelope(alpha, b"", received_at, 0))
        return alpha
