# EOS Lab Architecture

**Version:** 1.0  
**Status:** Active development  
**Primary objective:** a deterministic, event-driven market intelligence and execution system that can observe, interpret, evaluate, replay, simulate, and eventually execute trading decisions.

## System model

EOS is not a conventional `market data -> strategy -> order` bot. Every important state transition is represented by an event that can be recorded, inspected, and replayed.

```text
Market -> Observation -> Market State -> Microstructure -> Economics
       -> Risk / Decision -> Execution -> Outcome -> Learning
```

The same analytical pipeline must run in both modes:

```text
LIVE:    MT5 -> gateway -> EventBus -> engines
REPLAY:  event log -> replay adapter -> EventBus -> same engines
```

Analytical and decision components must not branch on whether data is live or replayed.

## Principles

1. **Event first.** Components communicate through typed events and subscribers, not gateway-to-engine calls.
2. **Immutable evidence.** `TickObserved` and its original payload are never altered after ingestion. Derived calculations are separate, lineage-linked events.
3. **Replayability.** Given the same events, configuration, and model version, deterministic components should reproduce the same outputs.
4. **Observation is not interpretation.** Market facts, model estimates, economic evaluation, decisions, and execution outcomes remain separate layers.
5. **Gateway is infrastructure.** It only receives, frames, decodes, envelopes, and publishes events. It contains no trading or model logic.
6. **Explicit uncertainty.** Level-1-derived quantities such as queue position, order-flow imbalance, and toxicity are estimates/proxies until validated against richer data. They carry algorithm/version and confidence metadata.
7. **No premature trading.** The progression is observation, measurement, interpretation, replay/backtest, simulation, paper trading, controlled capital, then production.

## Layers and event flow

| Layer | Responsibility | Primary input | Output |
| --- | --- | --- | --- |
| 0 — Observation | Capture market facts faithfully | MT5 tick | `TickObserved` |
| 1 — Market State | Maintain reconstructable rolling descriptive state | `TickObserved` | mutable `MarketState` |
| 2 — Microstructure | Estimate market mechanics and confidence | ticks + state | `MicrostructureEstimated` |
| 3 — Economics | Evaluate net economic value and uncertainty | microstructure + future models | `EconomicsEvaluated` |
| 4 — Risk / Decision | Independently constrain and select actions | economics + portfolio/risk state | `OrderRequested` |
| 5 — Execution | Submit and measure orders without silently changing decisions | `OrderRequested` | `OrderFilled` |
| 6 — Learning / Research | Build datasets, evaluate models, and falsify hypotheses | recorded events | research artifacts |

### Market-state contract

`MarketStateEngine` is mutable internal state, not evidence. It updates only from `TickObserved` in event order and can be rebuilt from the raw log. Its time basis is `exchange_time_ms` converted to UTC; it must never use process wall-clock time. With a configured window of the most recent *N* ticks, it exposes the latest quote, current spread, mean spread, population standard deviation of mid prices, total tick count, and tick rate `(window_count - 1) / elapsed_exchange_seconds`. A window with fewer than two ticks or a non-positive elapsed duration reports zero tick rate.

### Microstructure contract

`MicrostructureEstimator` currently implements `Level1Descriptive` version `1.0.0`. For each tick, it publishes a `MicrostructureEstimated` event whose first parent is that tick. `spread_bps = (ask - bid) / mid * 10,000`; `tick_to_vol_ratio = tick_rate / rolling_mid_price_volatility` when volatility is positive. It reports `None` for book imbalance, toxicity, and queue position because Level-1 ticks do not observe these values reliably. Both confidence fields remain `0.0`: this version is descriptive research instrumentation, not a validated trading signal.

### Economic-validation contract

`EconomicModelV1` consumes a microstructure event and explicit edge/cost estimates, publishing a lineage-linked `EconomicsEvaluated` event. Its V1 financial quantities are basis points. `NEV = E - C - lambda*sigma_C - gamma*sigma_E`; under the initial normal and independent-error assumptions, `PPE = Phi((E - C) / sqrt(sigma_E² + sigma_C² - 2*rho*sigma_E*sigma_C))`; and the execution budget is `E - gamma*sigma_E`. The gate approves only when `NEV > minimum_nev` and `PPE >= ppe_threshold`.

The versioned research parameters live in `config/economic_engine.json` (initially PPE 0.75, lambda 2.0, gamma 1.5, rho 0). `PrototypeEdgeModelV0` is disabled in that configuration, so the live system explicitly rejects with `MISSING_EDGE_ESTIMATE` until a real alpha model is supplied. Zero slippage and fee settings are an explicit small-order simulation assumption, never an implicit claim that execution is free. The initial normality, independence, no-impact, and threshold assumptions must be evaluated for calibration and falsified through replay research before any execution is enabled.

### Alpha contract

`AlphaEstimator` publishes an `AlphaEstimate` event for every microstructure event. It records expected edge, uncertainty, direction, horizon, algorithm identity, and the microstructure parent ID. The shipped `PrototypeEdgeModelV0` is disabled, therefore it emits `UNAVAILABLE / PROTOTYPE_EDGE_DISABLED`; this proves the wiring without claiming alpha. `EconomicEngine` joins alpha and microstructure events by that parent ID before evaluation, then records the economic event with the microstructure as its parent.

### Forward-outcome contract

`ForwardOutcomeLabeler` is a research subscriber. It joins each alpha event to its source tick through the microstructure lineage, then records the first observed tick at or beyond the alpha horizon. Its `realized_return_bps` is the signed mid-price return from the reference tick to that future tick. This is an outcome label, not execution P&L: it excludes fill price, fees, slippage, and market impact. It is persisted under `storage/derived/forward_outcomes` for future calibration experiments.

### Experiment contract

`experiment_runner.py` replays a framed raw log through the complete research pipeline and writes a new, empty experiment directory. Its manifest records the input/configuration SHA-256 hashes, model version, raw event count, and each subscriber's received, processed, dropped, and failure counts. `config/economic_engine.prototype.json` is for wiring research only: it enables a fixed 2 bps, 1-second, long prototype edge and must never be treated as a trading strategy.

### Runtime safety

Live subscribers expose queue depth, received/processed counts, drops, and failures through the EventBus health snapshot, which the gateway logs every 30 seconds. Economic joins expire unmatched signals after `max_signal_age_ms`; forward-outcome history is bounded to five minutes by default. On shutdown the gateway stops accepting new work, attempts to drain admitted events for ten seconds, then cancels workers. A drain timeout is visible in the gateway log rather than silently losing the condition.

### Application entry and trading boundary

`eos_app.py` is the only supported live runtime entry point. It loads one named profile from `config/eos_profiles.json` and builds the configured gateway subscriber graph. `research` is the only runnable mode today and explicitly disables execution. `paper` and `live` profiles intentionally refuse to start because account/portfolio observation, margin-aware RiskEngine, DecisionEngine, and a controlled execution adapter do not yet exist. EOS therefore does not currently consider account balance, equity, free margin, leverage, positions, orders, or broker constraints; these are required inputs before paper or live trading is enabled.

Derived events reference their inputs through lineage fields. For example, a `MicrostructureEstimated` event references the source `TickObserved` ID, and an `EconomicsEvaluated` event references the microstructure event ID. This makes every decision explainable from evidence.

## Current transport and event contract

`src/mql5/Experts/Observatory.mq5` is the Layer 0 producer. It observes MT5 ticks, builds `TickObserved`, and sends it through `SocketClient` to the Python gateway at `127.0.0.1:5555`.

Packets are little-endian and framed as:

```text
uint32 payload_size
byte[payload_size] payload
```

The active v1 tick payload is 428 bytes: 384-byte `EventMetadata` plus 44-byte tick data. The MQL5 structures and `src/python/protocol.py` / `src/python/decoder.py` are the executable source of truth. `docs/event-schema-v1.md` will contain the human-readable contract when that contract is formally finalized.

`EventEnvelope` preserves the decoded domain event, original payload, gateway UTC receipt time, and payload size. The envelope is transport evidence; the event represents domain meaning.

## Runtime topology

```text
MT5 Observatory
  -> TCP/Binary -> Gateway -> bounded ingestion queue -> Event dispatcher
                                                        |
             +--------------------+--------------------+--------------------+
             |                    |                    |                    |
       EventStore worker   Market-state worker  Microstructure worker  Monitoring worker
             |                    |                    |                    |
       immutable raw log     mutable state        derived event          telemetry
```

The EventBus owns one bounded ingestion queue and one bounded queue per subscriber. The gateway awaits only admission to the ingestion queue, preserving explicit upstream backpressure when the system is overloaded. Each subscriber runs independently; a slow or failed analytical subscriber cannot run in the gateway call stack or silently discard raw evidence.

Backpressure policy is explicit per subscription:

- Raw evidence uses `BLOCK`: it is never silently dropped; pressure propagates to the ingestion boundary.
- Derived analytics may use `DROP_NEWEST` when sampling/drop is an accepted, observable policy.
- Queue capacities, policy, drops, failures, and processing latency are operational metrics and must be monitored.

## Storage and replay

Raw payloads are append-only evidence. The current store writes framed records to `storage/<symbol>/<UTC-date>/tick.bin`; future layout is:

```text
storage/
  raw/<symbol>/...
  derived/microstructure/...
  derived/economics/...
  indexes/...
```

Derived research data can be regenerated. It must never overwrite raw evidence. A future SQLite/PostgreSQL layer may index metadata, experiments, and research outputs, but does not replace the event log as the historical authority.

The current derived store writes `storage/derived/microstructure/<symbol>/<UTC-date>/events.jsonl`. Each JSONL record includes the full event metadata, model identity, parent lineage, calculated values, and explicit `null` values for unsupported estimates. This format is research-oriented and intentionally separate from the binary raw evidence format.

Replay reads the same framed raw records and republishes envelopes into the same bus. Engines must therefore be deterministic, versioned, and input-source agnostic. The replay adapter derives the envelope timestamp from the event's exchange time because the current raw format stores the original payload and frame, not the original gateway receipt timestamp.

## Engineering rules

- Add capability through event subscribers; do not grow the gateway into an orchestrator.
- Every derived event identifies producer, algorithm, algorithm version, and schema version.
- Risk is an independently enforceable veto, never an implicit strategy detail.
- Execution records expected versus actual cost, slippage, commission, and outcomes.
- Model formulas (NEV, PPE, confidence, toxicity, and similar) must be defined and tested before their outputs are treated as intelligence.
- Test decoder/protocol contracts, event models, state calculations, queue isolation, replay, and deterministic repeated runs.

## Delivery sequence

1. Establish the isolated asynchronous EventBus and its contract.
2. Finalize and test `MarketStateEngine` in live and replay modes.
3. Add and validate `MicrostructureEstimator`; persist derived events.
4. Add `EconomicEngine`, with documented NEV/PPE hypotheses and simulation validation.
5. Add independently enforceable risk, decision, execution simulation, then paper trading.
6. Use event-based research to falsify hypotheses before production capital is considered.

The backbone is: **observe -> event log -> event bus -> engines -> derived events -> replay**.
