"""
market_state_engine.py

Maintains rolling market statistics.

This is the first analytical engine in EOS.
"""

from __future__ import annotations

import math
from datetime import datetime

from models import TickObserved
from .market_state import MarketState


class MarketStateEngine:

    WINDOW = 100

    def __init__(self):

        self.states: dict[str, MarketState] = {}

    def on_tick(self, tick: TickObserved):

        symbol = tick.meta.symbol

        if symbol not in self.states:
            self.states[symbol] = MarketState(symbol)

        state = self.states[symbol]

        # ------------------------
        # Latest values
        # ------------------------

        state.latest_bid = tick.bid
        state.latest_ask = tick.ask
        state.latest_mid = (tick.bid + tick.ask) / 2.0

        state.current_spread = tick.ask - tick.bid

        state.tick_count += 1
        state.last_update = datetime.now()

        # ------------------------
        # Rolling windows
        # ------------------------

        state.spreads.append(state.current_spread)
        state.mids.append(state.latest_mid)
        state.timestamps.append(datetime.now().timestamp())

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

            variance = (
                sum(
                    (x - mean) ** 2
                    for x in state.mids
                )
                / len(state.mids)
            )

            state.rolling_volatility = math.sqrt(variance)

        # ------------------------
        # Tick Rate
        # ------------------------

        if len(state.timestamps) > 1:

            elapsed = (
                state.timestamps[-1] -
                state.timestamps[0]
            )

            if elapsed > 0:

                state.ticks_per_second = (
                    len(state.timestamps) /
                    elapsed
                )

    def get(self, symbol: str) -> MarketState | None:

        return self.states.get(symbol)
