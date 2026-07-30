#!/usr/bin/env python3
"""
event_reader.py - Parses the binary MQL5 Event Store from Windows MT5.
"""
import os
import struct
import sys
from typing import Dict, Any
from datetime import datetime
import pandas as pd

# ------------------------------------------------------------------
# WSL Path to MT5 Common Files
# ------------------------------------------------------------------
EVENT_STORE_PATH = (
    "/mnt/c/Users/Nowayte/AppData/Roaming/MetaQuotes/"
    "Terminal/Common/Files/EventStore"
)

# ------------------------------------------------------------------
# MQL5 Struct Offsets
# ------------------------------------------------------------------
OFFSET_EVENT_TYPE = 64
OFFSET_EXCHANGE_TIME = 192
OFFSET_SYMBOL = 232

METADATA_SIZE = 512
PAYLOAD_TICK_SIZE = 44  # 4 doubles + ulong + uint

def read_cstring(data: bytes, offset: int, length: int) -> str:
    raw = data[offset:offset + length].split(b'\x00')[0]
    return raw.decode("utf-8", errors="ignore")


def parse_tick_event(data: bytes) -> Dict[str, Any]:
    if len(data) < METADATA_SIZE + PAYLOAD_TICK_SIZE:
        return None

    event_id = read_cstring(data, 0, 64)
    exchange_time = struct.unpack(
        "<Q",
        data[OFFSET_EXCHANGE_TIME:OFFSET_EXCHANGE_TIME + 8]
    )[0]
    symbol = read_cstring(data, OFFSET_SYMBOL, 12)

    payload = data[METADATA_SIZE:METADATA_SIZE + PAYLOAD_TICK_SIZE]
    bid, ask, last, vol_real, vol_tick, flags = struct.unpack(
        "<4dQI",
        payload
    )

    return {
        "event_id": event_id,
        "timestamp_ms": exchange_time,
        "datetime": datetime.fromtimestamp(exchange_time / 1000.0),
        "symbol": symbol,
        "bid": bid,
        "ask": ask,
        "spread_pips": (ask - bid) * 10000 if ask > 0 else 0,
        "last": last,
        "volume_tick": vol_tick,
    }


def stream_events(symbol: str, date_str: str = None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    filename = os.path.join(
        EVENT_STORE_PATH,
        f"{symbol}_{date_str}.evts"
    )

    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        print("Make sure the Observatory EA is running on MT5.")
        return

    print(f"Reading: {filename}")

    with open(filename, "rb") as f:
        while True:
            header = f.read(METADATA_SIZE)
            if not header:
                break

            ev_type = struct.unpack(
                "<H",
                header[OFFSET_EVENT_TYPE:OFFSET_EVENT_TYPE + 2]
            )[0]

            if ev_type == 0:
                payload = f.read(PAYLOAD_TICK_SIZE)
                if len(payload) < PAYLOAD_TICK_SIZE:
                    break

                parsed = parse_tick_event(header + payload)
                if parsed:
                    yield parsed
            else:
                print(f"Encountered unknown event type {ev_type}.")
                break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python event_reader.py <SYMBOL> [YYYYMMDD]")
        sys.exit(1)

    symbol = sys.argv[1]
    date_str = sys.argv[2] if len(sys.argv) > 2 else None

    events = []

    for ev in stream_events(symbol, date_str):
        print(
            f"{ev['datetime']} | "
            f"{ev['symbol']} | "
            f"Bid: {ev['bid']:.5f} | "
            f"Spread: {ev['spread_pips']:.1f} pips | "
            f"Vol: {ev['volume_tick']}"
        )

        events.append(ev)

        if len(events) >= 100:
            break

    if events:
        df = pd.DataFrame(events)

        print("\n--- Summary ---")
        print(df[["symbol", "bid", "ask", "spread_pips"]].describe())
