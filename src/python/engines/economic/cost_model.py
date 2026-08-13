from __future__ import annotations

from dataclasses import dataclass

from models import MicrostructureEstimated

from .config import EconomicConfig


@dataclass(frozen=True, slots=True)
class CostEstimate:
    spread_cost_bps: float
    slippage_cost_bps: float
    fee_cost_bps: float
    market_impact_cost_bps: float
    expected_cost_bps: float
    cost_uncertainty_bps: float


class Level1CostModel:
    """A disclosed small-order cost model based on observed spread plus config."""

    def __init__(self, config: EconomicConfig):
        self.config = config

    def estimate(self, microstructure: MicrostructureEstimated) -> CostEstimate | None:
        if microstructure.spread_bps is None or microstructure.spread_bps < 0:
            return None
        values = (
            microstructure.spread_bps,
            self.config.slippage_cost_bps,
            self.config.fee_cost_bps,
            self.config.cost_uncertainty_bps,
        )
        if any(value < 0 for value in values):
            return None
        spread_cost = microstructure.spread_bps * self.config.spread_cost_fraction
        impact = 0.0
        return CostEstimate(
            spread_cost_bps=spread_cost,
            slippage_cost_bps=self.config.slippage_cost_bps,
            fee_cost_bps=self.config.fee_cost_bps,
            market_impact_cost_bps=impact,
            expected_cost_bps=(
                spread_cost + self.config.slippage_cost_bps + self.config.fee_cost_bps + impact
            ),
            cost_uncertainty_bps=self.config.cost_uncertainty_bps,
        )
