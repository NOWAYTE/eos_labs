"""
models.py

EOS Domain Models
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================
# Event Metadata
# ============================================================

@dataclass(slots=True)
class EventMetadata:
    event_id: str

    event_type: int
    domain: int

    schema_major: int
    schema_minor: int

    exchange_time_ms: int
    local_time_ms: int
    monotonic_counter: int

    producer: str
    session_id: str
    symbol: str

    parent_id_1: str
    parent_id_2: str

    algorithm: str
    algorithm_version: str

    checksum: int


# ============================================================
# TickObserved
# ============================================================

@dataclass(slots=True)
class TickObserved:

    meta: EventMetadata

    bid: float
    ask: float
    last: float

    volume_real: float
    volume_tick: int

    flags: int


# ============================================================
# MicrostructureEstimated
# ============================================================

@dataclass(slots=True)
class MicrostructureEstimated:
    """A versioned interpretation derived from one ``TickObserved`` event.

    Values that Level-1 ticks cannot support are ``None`` rather than
    fabricated proxies. Their confidence is correspondingly zero.
    """

    meta: EventMetadata

    tick_to_vol_ratio: float | None
    spread_bps: float | None
    book_imbalance: float | None
    toxicity_score: float | None
    queue_position_est: int | None
    confidence_overall: float
    confidence_queue: float


@dataclass(slots=True)
class AlphaEstimate:
    """Explicit, versioned edge-model output; never a trading decision."""

    meta: EventMetadata
    expected_edge_bps: float | None
    edge_uncertainty_bps: float | None
    horizon_ms: int | None
    direction: int | None
    confidence: float
    outcome: str
    reason: str


@dataclass(slots=True)
class ForwardOutcomeRealized:
    """Observed future price movement used to evaluate an alpha hypothesis."""

    meta: EventMetadata
    direction: int
    horizon_ms: int
    reference_mid: float
    realized_mid: float
    realized_return_bps: float


# ============================================================
# EconomicsEvaluated
# ============================================================

@dataclass(slots=True)
class EconomicsEvaluated:
    """Auditable economic gate result; all V1 values are basis points."""

    meta: EventMetadata
    direction: int | None
    horizon_ms: int | None
    expected_edge_bps: float | None
    expected_cost_bps: float | None
    spread_cost_bps: float | None
    slippage_cost_bps: float | None
    fee_cost_bps: float | None
    market_impact_cost_bps: float | None
    edge_uncertainty_bps: float | None
    cost_uncertainty_bps: float | None
    edge_cost_correlation: float | None
    nev_bps: float | None
    ppe: float | None
    execution_budget_bps: float | None
    outcome: str
    reason: str
    model_version: str


# ============================================================
# BarClosed
# ============================================================

@dataclass(slots=True)
class BarClosed:

    meta: EventMetadata

    interval_sec: int

    open: float
    high: float
    low: float
    close: float

    tick_volume: int

    spread_avg: float
