#!/usr/bin/env python3
"""
gateway.py

EOS Gateway

Responsibilities
----------------
1. Accept TCP connections from MT5.
2. Read framed binary packets.
3. Decode packets into domain events.
4. Wrap them in an EventEnvelope.
5. Publish them onto the EventBus.

The gateway never performs analytics.
The gateway never performs storage directly.
"""

from __future__ import annotations

import asyncio
import json
import struct
from datetime import datetime, timezone

from decoder import decode_tick
from envelope import EventEnvelope
from event_bus import EventBus
from event_store import DerivedEventStore, EventStore
from models import AlphaEstimate, EconomicsEvaluated, ForwardOutcomeRealized, MicrostructureEstimated, TickObserved

# NEW
from engines.market_state_engine import MarketStateEngine
from engines.microstructure_estimator import MicrostructureEstimator
from engines.alpha_estimator import AlphaEstimator
from engines.forward_outcome_labeler import ForwardOutcomeLabeler
from engines.economic.engine import EconomicEngine
from engines.economic.config import EconomicConfig


HOST = "127.0.0.1"
PORT = 5555
DRAIN_TIMEOUT_SECONDS = 10
HEALTH_INTERVAL_SECONDS = 30


# ============================================================
# Runtime Components
# ============================================================

bus: EventBus | None = None


def configure_runtime(economic_config: str | None = None) -> EventBus:
    """Build one configured subscriber graph for a gateway process."""
    runtime_bus = EventBus()
    config = EconomicConfig.from_file(economic_config) if economic_config else EconomicConfig.from_file()
    store = EventStore()
    derived_store = DerivedEventStore()
    market_state = MarketStateEngine()
    microstructure = MicrostructureEstimator(bus=runtime_bus)
    alpha = AlphaEstimator(bus=runtime_bus, config=config)
    outcome_labeler = ForwardOutcomeLabeler(bus=runtime_bus)
    economics = EconomicEngine(bus=runtime_bus, config=config)

    runtime_bus.subscribe(TickObserved, store.on_tick, receive_envelope=True)
    runtime_bus.subscribe(TickObserved, market_state.on_tick)
    runtime_bus.subscribe(TickObserved, microstructure.on_tick)
    runtime_bus.subscribe(TickObserved, outcome_labeler.on_tick)
    runtime_bus.subscribe(MicrostructureEstimated, derived_store.on_microstructure)
    runtime_bus.subscribe(MicrostructureEstimated, economics.on_microstructure)
    runtime_bus.subscribe(MicrostructureEstimated, alpha.on_microstructure)
    runtime_bus.subscribe(MicrostructureEstimated, outcome_labeler.on_microstructure)
    runtime_bus.subscribe(AlphaEstimate, derived_store.on_alpha)
    runtime_bus.subscribe(AlphaEstimate, economics.on_alpha)
    runtime_bus.subscribe(AlphaEstimate, outcome_labeler.on_alpha)
    runtime_bus.subscribe(EconomicsEvaluated, derived_store.on_economics)
    runtime_bus.subscribe(ForwardOutcomeRealized, derived_store.on_forward_outcome)
    return runtime_bus


# ============================================================
# Client Handler
# ============================================================

async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
):

    addr = writer.get_extra_info("peername")

    print(f"[+] MT5 connected: {addr}")

    packets = 0

    try:

        while True:

            #
            # Read packet size
            #

            header = await reader.readexactly(4)

            packet_size = struct.unpack("<I", header)[0]

            #
            # Read payload
            #

            payload = await reader.readexactly(packet_size)

            #
            # Decode
            #

            event = decode_tick(payload)

            #
            # Wrap
            #

            envelope = EventEnvelope(
                event=event,
                payload=payload,
                received_at=datetime.now(timezone.utc),
                size=len(payload),
            )

            #
            # Publish
            #

            assert bus is not None
            await bus.publish(envelope)

            packets += 1

    except asyncio.IncompleteReadError:

        print("Client disconnected.")

    except Exception as e:

        print("Gateway error:", e)

    finally:

        writer.close()

        await writer.wait_closed()

        print("[-] Connection closed")


# ============================================================
# Main
# ============================================================

async def main(
    host: str = HOST,
    port: int = PORT,
    economic_config: str | None = None,
):
    global bus
    bus = configure_runtime(economic_config)
    await bus.start()
    health_task = asyncio.create_task(report_health())
    try:
        server = await asyncio.start_server(
            handle_client,
            host,
            port,
        )

        print(f"EOS Gateway listening on {host}:{port}")

        async with server:
            await server.serve_forever()
    finally:
        health_task.cancel()
        await asyncio.gather(health_task, return_exceptions=True)
        try:
            await asyncio.wait_for(bus.join(), timeout=DRAIN_TIMEOUT_SECONDS)
        except TimeoutError:
            print("Gateway drain timed out; stopping workers with events still pending")
        await bus.stop()


async def report_health():
    while True:
        await asyncio.sleep(HEALTH_INTERVAL_SECONDS)
        assert bus is not None
        print("EOS health " + json.dumps(bus.metrics(), sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
