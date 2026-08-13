"""
market_state.py

Internal rolling market state.

This is NOT an immutable event.

It is the continuously updated state of a symbol that
analytical engines can read.
"""

from collections import deque
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class MarketState:
    """Mutable, reconstructable state for one symbol.

    The deques contain only values derived from ``TickObserved`` in event
    order. They intentionally use exchange timestamps rather than process
    clock time, allowing replay to reproduce the same state.
    """

    symbol: str

    latest_bid: float = 0.0
    latest_ask: float = 0.0
    latest_mid: float = 0.0

    current_spread: float = 0.0
    average_spread: float = 0.0

    rolling_volatility: float = 0.0

    tick_count: int = 0

    ticks_per_second: float = 0.0

    last_update: datetime | None = None

    spreads: deque[float] = field(default_factory=deque)

    mids: deque[float] = field(default_factory=deque)

    timestamps: deque[float] = field(default_factory=deque)
