"""
market_state_engine.py

Maintains rolling market statistics.

This is the first analytical engine in EOS.
"""

from __future__ import annotations

import math
from collections import deque
from datetime import UTC, datetime

from models import TickObserved
from .market_state import MarketState


class MarketStateEngine:
    """Build deterministic rolling market state from ``TickObserved`` events.

    The rolling volatility is the population standard deviation of mid prices.
    Tick rate is ``(window_count - 1) / elapsed_exchange_seconds``. A window
    with fewer than two ticks, or non-positive elapsed time, has a zero rate.
    """

    DEFAULT_WINDOW_SIZE = 100

    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE):
        if window_size <= 0:
            raise ValueError("window_size must be greater than zero")

        self.window_size = window_size
        self.states: dict[str, MarketState] = {}

    def on_tick(self, tick: TickObserved) -> MarketState:
        symbol = tick.meta.symbol

        if symbol not in self.states:
            self.states[symbol] = MarketState(
                symbol=symbol,
                spreads=deque(maxlen=self.window_size),
                mids=deque(maxlen=self.window_size),
                timestamps=deque(maxlen=self.window_size),
            )

        state = self.states[symbol]

        # ------------------------
        # Latest values
        # ------------------------

        state.latest_bid = tick.bid
        state.latest_ask = tick.ask
        state.latest_mid = (tick.bid + tick.ask) / 2.0

        state.current_spread = tick.ask - tick.bid

        state.tick_count += 1
        state.last_update = datetime.fromtimestamp(
            tick.meta.exchange_time_ms / 1_000,
            tz=UTC,
        )

        # ------------------------
        # Rolling windows
        # ------------------------

        state.spreads.append(state.current_spread)
        state.mids.append(state.latest_mid)
        state.timestamps.append(tick.meta.exchange_time_ms / 1_000)

        # ------------------------
        # Average spread
        # ------------------------

        if state.spreads:
            state.average_spread = (
                sum(state.spreads) /
                len(state.spreads)
            )

        # ------------------------
        # Rolling volatility
        # ------------------------

        if len(state.mids) > 1:
            mean = sum(state.mids) / len(state.mids)
            variance = sum((mid - mean) ** 2 for mid in state.mids) / len(state.mids)
            state.rolling_volatility = math.sqrt(variance)
        else:
            state.rolling_volatility = 0.0

        # ------------------------
        # Tick Rate
        # ------------------------

        if len(state.timestamps) > 1:
            elapsed = state.timestamps[-1] - state.timestamps[0]
            state.ticks_per_second = (
                (len(state.timestamps) - 1) / elapsed if elapsed > 0 else 0.0
            )
        else:
            state.ticks_per_second = 0.0

        return state

    def get(self, symbol: str) -> MarketState | None:
        return self.states.get(symbol)
