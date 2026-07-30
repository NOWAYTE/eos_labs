"""
market_state.py

Internal rolling market state.

This is NOT an immutable event.

It is the continuously updated state of a symbol that
analytical engines can read.
"""

from dataclasses import dataclass, field
from collections import deque
from datetime import datetime


@dataclass
class MarketState:

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

    spreads: deque = field(default_factory=lambda: deque(maxlen=100))

    mids: deque = field(default_factory=lambda: deque(maxlen=100))

    timestamps: deque = field(default_factory=lambda: deque(maxlen=100))
