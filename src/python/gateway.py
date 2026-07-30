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
import struct
from datetime import datetime

from decoder import decode_tick
from envelope import EventEnvelope
from event_bus import EventBus
from event_store import EventStore
from models import TickObserved

# NEW
from engines.market_state_engine import MarketStateEngine


HOST = "127.0.0.1"
PORT = 5555


# ============================================================
# Runtime Components
# ============================================================

bus = EventBus()

store = EventStore()

market_state = MarketStateEngine()


# ============================================================
# EventBus Subscriptions
# ============================================================

bus.subscribe(
    TickObserved,
    store.on_tick,
)

bus.subscribe(
    TickObserved,
    market_state.on_tick,
)


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
                received_at=datetime.utcnow(),
                size=len(payload),
            )

            #
            # Publish
            #

            bus.publish(envelope)

            packets += 1

            #
            # Temporary console output
            #

            print(
                f"[{packets:06d}] "
                f"{event.meta.event_id} "
                f"{event.meta.symbol} "
                f"Bid={event.bid:.5f} "
                f"Ask={event.ask:.5f}"
            )

            #
            # Temporary Market State dump
            #
            # Remove once MicrostructureEstimator exists.
            #

            state = market_state.get(event.meta.symbol)

            if state and state.tick_count % 25 == 0:

                print(
                    f"""
---------------- Market State ----------------

Symbol              : {state.symbol}

Bid                 : {state.latest_bid:.5f}
Ask                 : {state.latest_ask:.5f}
Mid                 : {state.latest_mid:.5f}

Spread              : {state.current_spread:.5f}
Average Spread      : {state.average_spread:.5f}

Volatility          : {state.rolling_volatility:.8f}

Ticks               : {state.tick_count}
Ticks / Second      : {state.ticks_per_second:.2f}

----------------------------------------------
"""
                )

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

async def main():

    server = await asyncio.start_server(
        handle_client,
        HOST,
        PORT,
    )

    print(f"EOS Gateway listening on {HOST}:{PORT}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
