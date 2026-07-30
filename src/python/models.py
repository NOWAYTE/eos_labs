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
