"""
Canonical EOS event models.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class EventMetadata:
    event_id: str
    event_type: int
    exchange_time_ms: int
    producer: str
    stream_id: str
    symbol: str

    @property
    def timestamp(self) -> datetime:
        return datetime.fromtimestamp(self.exchange_time_ms / 1000.0)


@dataclass(slots=True)
class TickObserved:
    metadata: EventMetadata

    bid: float
    ask: float
    last: float

    volume_real: float
    volume_tick: int

    flags: int

    @property
    def spread(self) -> float:
        return self.ask - self.bid

    @property
    def spread_pips(self) -> float:
        return (self.ask - self.bid) * 10000.0
