from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EconomicConfig:
    """Versioned research parameters for ``EconomicModelV1``.

    All monetary quantities in this first model are basis points. Zero fees
    and slippage are allowed only because the checked-in configuration names
    this as an explicit small-order simulation assumption.
    """

    model_version: str = "EconomicModelV1"
    ppe_threshold: float = 0.75
    lambda_cost_uncertainty: float = 2.0
    gamma_edge_uncertainty: float = 1.5
    edge_cost_correlation: float = 0.0
    spread_cost_fraction: float = 0.5
    slippage_cost_bps: float = 0.0
    fee_cost_bps: float = 0.0
    cost_uncertainty_bps: float = 0.0
    include_market_impact: bool = False
    max_signal_age_ms: int = 500
    minimum_nev_bps: float = 0.0
    prototype_edge_enabled: bool = False
    prototype_expected_edge_bps: float | None = None
    prototype_edge_uncertainty_bps: float | None = None
    prototype_horizon_ms: int = 500
    prototype_direction: int | None = None

    @classmethod
    def from_file(cls, filename: str | Path | None = None) -> "EconomicConfig":
        if filename is None:
            filename = Path(__file__).parents[4] / "config" / "economic_engine.json"
        with Path(filename).open(encoding="utf-8") as stream:
            return cls(**json.load(stream))
