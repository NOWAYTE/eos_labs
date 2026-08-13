from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from models import MicrostructureEstimated


@dataclass(frozen=True, slots=True)
class EdgeEstimate:
    """An explicit alpha-model output, expressed in basis points."""

    expected_edge_bps: float
    edge_uncertainty_bps: float
    horizon_ms: int
    direction: int
    algorithm: str
    algorithm_version: str


class EdgeModel(Protocol):
    def estimate(self, microstructure: MicrostructureEstimated) -> EdgeEstimate | None: ...


class PrototypeEdgeModelV0:
    """Research-only configurable edge source; never represents validated alpha."""

    ALGORITHM = "PrototypeEdgeModel"
    VERSION = "0.0.0"

    def __init__(
        self,
        *,
        enabled: bool,
        expected_edge_bps: float | None,
        edge_uncertainty_bps: float | None,
        horizon_ms: int,
        direction: int | None,
    ):
        self.enabled = enabled
        self.expected_edge_bps = expected_edge_bps
        self.edge_uncertainty_bps = edge_uncertainty_bps
        self.horizon_ms = horizon_ms
        self.direction = direction

    def estimate(self, microstructure: MicrostructureEstimated) -> EdgeEstimate | None:
        if not self.enabled:
            return None
        if (
            self.expected_edge_bps is None
            or self.edge_uncertainty_bps is None
            or self.direction not in (-1, 1)
            or self.horizon_ms <= 0
        ):
            return None
        return EdgeEstimate(
            expected_edge_bps=self.expected_edge_bps,
            edge_uncertainty_bps=self.edge_uncertainty_bps,
            horizon_ms=self.horizon_ms,
            direction=self.direction,
            algorithm=self.ALGORITHM,
            algorithm_version=self.VERSION,
        )
