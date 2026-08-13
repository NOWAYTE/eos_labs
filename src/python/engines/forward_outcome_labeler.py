"""Label alpha estimates with the first observed tick at or beyond their horizon."""

from __future__ import annotations

from datetime import UTC, datetime

from envelope import EventEnvelope
from event_bus import EventBus
from models import (
    AlphaEstimate,
    EventMetadata,
    ForwardOutcomeRealized,
    MicrostructureEstimated,
    TickObserved,
)


class ForwardOutcomeLabeler:
    """Research-only labeler; it observes, but never predicts, future returns."""

    def __init__(self, bus: EventBus | None = None, retention_ms: int = 300_000):
        self.bus = bus
        self.retention_ms = retention_ms
        self._ticks: dict[str, TickObserved] = {}
        self._history: dict[str, list[TickObserved]] = {}
        self._micro_to_tick: dict[str, str] = {}
        self._pending_alpha: dict[str, AlphaEstimate] = {}
        self._pending: dict[str, tuple[AlphaEstimate, TickObserved]] = {}

    async def on_tick(self, tick: TickObserved) -> None:
        self._ticks[tick.meta.event_id] = tick
        history = self._history.setdefault(tick.meta.symbol, [])
        history.append(tick)
        self._prune(tick.meta.exchange_time_ms)
        await self._label_ready(tick.meta.symbol)

    async def on_microstructure(self, micro: MicrostructureEstimated) -> None:
        self._micro_to_tick[micro.meta.event_id] = micro.meta.parent_id_1
        alpha = self._pending_alpha.pop(micro.meta.event_id, None)
        if alpha is not None:
            self._register(alpha)

    async def on_alpha(self, alpha: AlphaEstimate) -> None:
        self._register(alpha)

    def _register(self, alpha: AlphaEstimate) -> None:
        tick_id = self._micro_to_tick.get(alpha.meta.parent_id_1)
        if tick_id is None:
            self._pending_alpha[alpha.meta.parent_id_1] = alpha
            return
        tick = self._ticks.get(tick_id)
        if tick is not None and alpha.horizon_ms and alpha.direction in (-1, 1):
            self._pending[alpha.meta.event_id] = (alpha, tick)

    async def _label_ready(self, symbol: str) -> None:
        history = self._history[symbol]
        ready = []
        for alpha_id, (alpha, reference) in self._pending.items():
            if reference.meta.symbol != symbol:
                continue
            target = reference.meta.exchange_time_ms + alpha.horizon_ms
            future = next(
                (tick for tick in history if tick.meta.exchange_time_ms >= target),
                None,
            )
            if future is not None:
                ready.append((alpha_id, alpha, reference, future))
        for alpha_id, alpha, reference, future in ready:
            del self._pending[alpha_id]
            await self._publish(self._label(alpha, reference, future))

    def _prune(self, now_ms: int) -> None:
        cutoff = now_ms - self.retention_ms
        for symbol, history in self._history.items():
            self._history[symbol] = [tick for tick in history if tick.meta.exchange_time_ms >= cutoff]
        self._ticks = {
            key: tick for key, tick in self._ticks.items()
            if tick.meta.exchange_time_ms >= cutoff
        }
        self._micro_to_tick = {
            key: tick_id for key, tick_id in self._micro_to_tick.items()
            if tick_id in self._ticks
        }
        self._pending = {
            key: value for key, value in self._pending.items()
            if value[1].meta.exchange_time_ms >= cutoff
        }

    def _label(
        self,
        alpha: AlphaEstimate,
        reference: TickObserved,
        future: TickObserved,
    ) -> ForwardOutcomeRealized:
        reference_mid = (reference.bid + reference.ask) / 2
        realized_mid = (future.bid + future.ask) / 2
        return_bps = ((realized_mid - reference_mid) / reference_mid) * 10_000
        return ForwardOutcomeRealized(
            meta=EventMetadata(
                event_id=f"outcome:{alpha.meta.event_id}:{future.meta.event_id}",
                event_type=2, domain=1, schema_major=1, schema_minor=0,
                exchange_time_ms=future.meta.exchange_time_ms,
                local_time_ms=future.meta.local_time_ms,
                monotonic_counter=future.meta.monotonic_counter,
                producer="ForwardOutcomeLabeler", session_id=alpha.meta.session_id,
                symbol=alpha.meta.symbol, parent_id_1=alpha.meta.event_id,
                parent_id_2=reference.meta.event_id, algorithm="ForwardMidReturn",
                algorithm_version="1.0.0", checksum=0,
            ),
            direction=alpha.direction,
            horizon_ms=alpha.horizon_ms,
            reference_mid=reference_mid,
            realized_mid=realized_mid,
            realized_return_bps=alpha.direction * return_bps,
        )

    async def _publish(self, outcome: ForwardOutcomeRealized) -> None:
        if self.bus is not None:
            received_at = datetime.fromtimestamp(outcome.meta.exchange_time_ms / 1_000, tz=UTC)
            await self.bus.publish(EventEnvelope(outcome, b"", received_at, 0))
