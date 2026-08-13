from __future__ import annotations

import math
from datetime import UTC, datetime

from envelope import EventEnvelope
from event_bus import EventBus
from models import AlphaEstimate, EconomicsEvaluated, EventMetadata, MicrostructureEstimated

from .config import EconomicConfig
from .cost_model import CostEstimate, Level1CostModel
from .edge_model import EdgeEstimate, EdgeModel, PrototypeEdgeModelV0
from .execution_budget import calculate_execution_budget_bps
from .gate import approve
from .nev import calculate_nev
from .ppe import calculate_ppe


class EconomicEngine:
    """Validate explicit edge and cost estimates; never invent missing inputs."""

    PRODUCER = "EconomicEngine"
    ALGORITHM = "EconomicModel"

    def __init__(
        self,
        bus: EventBus | None = None,
        config: EconomicConfig | None = None,
        edge_model: EdgeModel | None = None,
        cost_model: Level1CostModel | None = None,
    ):
        self.bus = bus
        self.config = config or EconomicConfig.from_file()
        self.edge_model = edge_model or PrototypeEdgeModelV0(
            enabled=self.config.prototype_edge_enabled,
            expected_edge_bps=self.config.prototype_expected_edge_bps,
            edge_uncertainty_bps=self.config.prototype_edge_uncertainty_bps,
            horizon_ms=self.config.prototype_horizon_ms,
            direction=self.config.prototype_direction,
        )
        self.cost_model = cost_model or Level1CostModel(self.config)
        self._microstructure: dict[str, MicrostructureEstimated] = {}
        self._alpha: dict[str, AlphaEstimate] = {}

    def evaluate(
        self, microstructure: MicrostructureEstimated, alpha: AlphaEstimate | None = None
    ) -> EconomicsEvaluated:
        edge = self._edge_from_alpha(alpha) if alpha is not None else self.edge_model.estimate(microstructure)
        cost = self.cost_model.estimate(microstructure)
        reason = self._validate(edge, cost)
        if reason is not None:
            return self._result(microstructure, edge, cost, outcome="REJECTED", reason=reason)

        assert edge is not None
        assert cost is not None
        nev = calculate_nev(
            edge.expected_edge_bps,
            cost.expected_cost_bps,
            edge.edge_uncertainty_bps,
            cost.cost_uncertainty_bps,
            self.config,
        )
        ppe = calculate_ppe(
            edge.expected_edge_bps,
            cost.expected_cost_bps,
            edge.edge_uncertainty_bps,
            cost.cost_uncertainty_bps,
            self.config.edge_cost_correlation,
        )
        budget = calculate_execution_budget_bps(
            edge.expected_edge_bps,
            edge.edge_uncertainty_bps,
            self.config,
        )
        if ppe is None:
            return self._result(
                microstructure, edge, cost, outcome="REJECTED", reason="INVALID_NET_UNCERTAINTY",
                nev=nev, budget=budget,
            )
        outcome = "APPROVED" if approve(nev, ppe, self.config) else "REJECTED"
        reason = "ECONOMIC_GATE_PASSED" if outcome == "APPROVED" else "ECONOMIC_GATE_FAILED"
        return self._result(
            microstructure, edge, cost, outcome=outcome, reason=reason,
            nev=nev, ppe=ppe, budget=budget,
        )

    async def on_microstructure(
        self,
        microstructure: MicrostructureEstimated,
    ) -> None:
        self._prune(microstructure.meta.exchange_time_ms)
        self._microstructure[microstructure.meta.event_id] = microstructure
        await self._evaluate_pair(microstructure.meta.event_id)

    async def on_alpha(self, alpha: AlphaEstimate) -> None:
        self._prune(alpha.meta.exchange_time_ms)
        self._alpha[alpha.meta.parent_id_1] = alpha
        await self._evaluate_pair(alpha.meta.parent_id_1)

    async def _evaluate_pair(self, micro_id: str) -> None:
        micro = self._microstructure.get(micro_id)
        alpha = self._alpha.get(micro_id)
        if micro is None or alpha is None:
            return
        result = self.evaluate(micro, alpha)
        del self._microstructure[micro_id]
        del self._alpha[micro_id]
        if self.bus is not None:
            received_at = datetime.fromtimestamp(micro.meta.exchange_time_ms / 1_000, tz=UTC)
            await self.bus.publish(EventEnvelope(result, b"", received_at, 0))

    def _prune(self, now_ms: int) -> None:
        cutoff = now_ms - self.config.max_signal_age_ms
        self._microstructure = {
            key: value for key, value in self._microstructure.items()
            if value.meta.exchange_time_ms >= cutoff
        }
        self._alpha = {
            key: value for key, value in self._alpha.items()
            if value.meta.exchange_time_ms >= cutoff
        }

    @staticmethod
    def _edge_from_alpha(alpha: AlphaEstimate) -> EdgeEstimate | None:
        if (
            alpha.expected_edge_bps is None or alpha.edge_uncertainty_bps is None
            or alpha.horizon_ms is None or alpha.direction is None
        ):
            return None
        return EdgeEstimate(
            alpha.expected_edge_bps, alpha.edge_uncertainty_bps, alpha.horizon_ms,
            alpha.direction, alpha.meta.algorithm, alpha.meta.algorithm_version,
        )

    def _validate(self, edge: EdgeEstimate | None, cost: CostEstimate | None) -> str | None:
        if edge is None:
            return "MISSING_EDGE_ESTIMATE"
        if cost is None:
            return "MISSING_COST_ESTIMATE"
        if edge.horizon_ms <= 0 or edge.direction not in (-1, 1):
            return "INVALID_EDGE_ESTIMATE"
        if not all(math.isfinite(value) and value >= 0 for value in (
            edge.expected_edge_bps, edge.edge_uncertainty_bps,
            cost.expected_cost_bps, cost.cost_uncertainty_bps,
        )):
            return "INVALID_ECONOMIC_INPUT"
        if not -1 <= self.config.edge_cost_correlation <= 1:
            return "INVALID_EDGE_COST_CORRELATION"
        return None

    def _result(
        self,
        microstructure: MicrostructureEstimated,
        edge: EdgeEstimate | None,
        cost: CostEstimate | None,
        *,
        outcome: str,
        reason: str,
        nev: float | None = None,
        ppe: float | None = None,
        budget: float | None = None,
    ) -> EconomicsEvaluated:
        return EconomicsEvaluated(
            meta=EventMetadata(
                event_id=(f"econ:{microstructure.meta.event_id}:{self.config.model_version}"),
                event_type=1, domain=1, schema_major=1, schema_minor=0,
                exchange_time_ms=microstructure.meta.exchange_time_ms,
                local_time_ms=microstructure.meta.local_time_ms,
                monotonic_counter=microstructure.meta.monotonic_counter,
                producer=self.PRODUCER, session_id=microstructure.meta.session_id,
                symbol=microstructure.meta.symbol,
                parent_id_1=microstructure.meta.event_id,
                parent_id_2="", algorithm=self.ALGORITHM,
                algorithm_version=self.config.model_version, checksum=0,
            ),
            direction=edge.direction if edge else None,
            horizon_ms=edge.horizon_ms if edge else None,
            expected_edge_bps=edge.expected_edge_bps if edge else None,
            expected_cost_bps=cost.expected_cost_bps if cost else None,
            spread_cost_bps=cost.spread_cost_bps if cost else None,
            slippage_cost_bps=cost.slippage_cost_bps if cost else None,
            fee_cost_bps=cost.fee_cost_bps if cost else None,
            market_impact_cost_bps=cost.market_impact_cost_bps if cost else None,
            edge_uncertainty_bps=edge.edge_uncertainty_bps if edge else None,
            cost_uncertainty_bps=cost.cost_uncertainty_bps if cost else None,
            edge_cost_correlation=self.config.edge_cost_correlation,
            nev_bps=nev, ppe=ppe, execution_budget_bps=budget,
            outcome=outcome, reason=reason, model_version=self.config.model_version,
        )
