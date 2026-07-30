#!/usr/bin/env python3
"""
inspect_event_file.py

Binary inspection utility for EOS Lab EventStore files.

This does NOT attempt to parse the events.
It simply shows exactly what MT5 wrote so we can derive the
true binary layout of EventMetadata.
"""

import os
import sys


EVENT_STORE = (
    "/mnt/c/Users/Nowayte/AppData/Roaming/"
    "MetaQuotes/Terminal/Common/Files/EventStore"
)


def hexdump(data: bytes, start=0):
    """Pretty hex dump."""

    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]

        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

        print(f"{start + offset:08X}  {hex_part:<48} |{ascii_part}|")


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print("    python inspect_event_file.py EURUSD")
        sys.exit(1)

    symbol = sys.argv[1]

    from datetime import datetime

    date = datetime.now().strftime("%Y%m%d")

    filename = os.path.join(
        EVENT_STORE,
        f"{symbol}_{date}.evts"
    )

    print()
    print("File:", filename)

    if not os.path.exists(filename):
        print("Not found.")
        sys.exit(1)

    size = os.path.getsize(filename)

    print("Size:", size, "bytes")

    print()

    with open(filename, "rb") as f:

        first = f.read(640)

    print("First", len(first), "bytes")
    print()

    hexdump(first)


if __name__ == "__main__":
    main()
