"""
protocol.py
EOS Binary Protocol v1

Single source of truth for binary event layouts.
"""

from __future__ import annotations

import struct

# ============================================================
# Schema
# ============================================================

SCHEMA_MAJOR = 1
SCHEMA_MINOR = 0

# ============================================================
# Sizes (must match MT5)
# ============================================================

EVENT_METADATA_SIZE = 384
TICK_OBSERVED_SIZE = 428
BAR_CLOSED_SIZE = 436

# ============================================================
# Primitive Structs
# ============================================================

UINT16 = struct.Struct("<H")
UINT32 = struct.Struct("<I")
UINT64 = struct.Struct("<Q")
DOUBLE = struct.Struct("<d")

# ============================================================
# Packet Header
# ============================================================

#
# Every packet received from MT5 is:
#
# uint32 payload_size
# uchar[payload_size]
#

PACKET_HEADER = UINT32

# ============================================================
# Metadata offsets
# ============================================================

EVENT_ID_OFFSET = 0
EVENT_ID_SIZE = 64

EVENT_TYPE_OFFSET = 64
DOMAIN_OFFSET = 66

SCHEMA_MAJOR_OFFSET = 68
SCHEMA_MINOR_OFFSET = 70

EXCHANGE_TIME_OFFSET = 72
LOCAL_TIME_OFFSET = 80
MONOTONIC_COUNTER_OFFSET = 88

PRODUCER_OFFSET = 96
PRODUCER_SIZE = 32

SESSION_ID_OFFSET = 128
SESSION_ID_SIZE = 64

SYMBOL_OFFSET = 192
SYMBOL_SIZE = 12

PARENT1_OFFSET = 204
PARENT1_SIZE = 64

PARENT2_OFFSET = 268
PARENT2_SIZE = 64

ALGORITHM_OFFSET = 332
ALGORITHM_SIZE = 32

ALGO_VERSION_OFFSET = 364
ALGO_VERSION_SIZE = 16

CHECKSUM_OFFSET = 380

# ============================================================
# TickObserved payload offsets
# ============================================================

PAYLOAD = EVENT_METADATA_SIZE

BID_OFFSET = PAYLOAD + 0
ASK_OFFSET = PAYLOAD + 8
LAST_OFFSET = PAYLOAD + 16
VOLUME_REAL_OFFSET = PAYLOAD + 24
VOLUME_TICK_OFFSET = PAYLOAD + 32
FLAGS_OFFSET = PAYLOAD + 40
