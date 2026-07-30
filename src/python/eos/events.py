from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TickEvent:
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    volume: int

    @property
    def spread(self):
        return self.ask - self.bid
