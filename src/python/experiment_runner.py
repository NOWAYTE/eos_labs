#!/usr/bin/env python3
"""Run the complete EOS research pipeline against a framed raw tick log."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from engines.alpha_estimator import AlphaEstimator
from engines.economic.config import EconomicConfig
from engines.economic.engine import EconomicEngine
from engines.forward_outcome_labeler import ForwardOutcomeLabeler
from engines.microstructure_estimator import MicrostructureEstimator
from event_bus import EventBus
from event_store import DerivedEventStore
from models import AlphaEstimate, EconomicsEvaluated, ForwardOutcomeRealized, MicrostructureEstimated, TickObserved
from replay import Replay


def digest(filename: Path) -> str:
    return hashlib.sha256(filename.read_bytes()).hexdigest()


async def run(input_file: Path, config_file: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Experiment output must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    config = EconomicConfig.from_file(config_file)
    bus = EventBus()
    store = DerivedEventStore(output / "derived")
    micro = MicrostructureEstimator(bus=bus)
    alpha = AlphaEstimator(bus=bus, config=config)
    economics = EconomicEngine(bus=bus, config=config)
    outcomes = ForwardOutcomeLabeler(bus=bus)

    subscriptions = [
        bus.subscribe(TickObserved, micro.on_tick),
        bus.subscribe(TickObserved, outcomes.on_tick),
        bus.subscribe(MicrostructureEstimated, store.on_microstructure),
        bus.subscribe(MicrostructureEstimated, alpha.on_microstructure),
        bus.subscribe(MicrostructureEstimated, economics.on_microstructure),
        bus.subscribe(MicrostructureEstimated, outcomes.on_microstructure),
        bus.subscribe(AlphaEstimate, store.on_alpha),
        bus.subscribe(AlphaEstimate, economics.on_alpha),
        bus.subscribe(AlphaEstimate, outcomes.on_alpha),
        bus.subscribe(EconomicsEvaluated, store.on_economics),
        bus.subscribe(ForwardOutcomeRealized, store.on_forward_outcome),
    ]
    await bus.start()
    try:
        raw_events = await Replay(input_file).publish(bus)
        await bus.join()
    finally:
        await bus.stop()

    manifest = {
        "kind": "EOS experiment manifest",
        "created_at": datetime.now(UTC).isoformat(),
        "input_file": str(input_file.resolve()),
        "input_sha256": digest(input_file),
        "config_file": str(config_file.resolve()),
        "config_sha256": digest(config_file),
        "model_version": config.model_version,
        "raw_events": raw_events,
        "subscriptions": [
            {
                "event_type": subscription.event_type.__name__,
                "handler": getattr(subscription.handler, "__qualname__", repr(subscription.handler)),
                "received": subscription.received,
                "processed": subscription.processed,
                "dropped": subscription.dropped,
                "failures": subscription.failures,
            }
            for subscription in subscriptions
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an EOS replay experiment")
    parser.add_argument("input", type=Path, help="Framed raw tick.bin input")
    parser.add_argument("--config", type=Path, required=True, help="Economic/alpha experiment config")
    parser.add_argument("--output", type=Path, required=True, help="New empty experiment output directory")
    arguments = parser.parse_args()
    manifest = asyncio.run(run(arguments.input, arguments.config, arguments.output))
    print(f"Completed {manifest['raw_events']} raw events: {arguments.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
