"""
decoder.py

EOS Binary Decoder
"""

from __future__ import annotations

import struct

from protocol import *

from models import (
    EventMetadata,
    TickObserved,
)


# ============================================================
# Helpers
# ============================================================

def _cstring(data: bytes) -> str:
    """
    Decode a fixed-length C string.
    """

    return data.split(b"\x00", 1)[0].decode("ascii")


# ============================================================
# Metadata Decoder
# ============================================================

def decode_metadata(payload: bytes) -> EventMetadata:

    return EventMetadata(

        event_id=_cstring(
            payload[
                EVENT_ID_OFFSET:
                EVENT_ID_OFFSET + EVENT_ID_SIZE
            ]
        ),

        event_type=UINT16.unpack_from(payload, EVENT_TYPE_OFFSET)[0],

        domain=UINT16.unpack_from(payload, DOMAIN_OFFSET)[0],

        schema_major=UINT16.unpack_from(
            payload,
            SCHEMA_MAJOR_OFFSET,
        )[0],

        schema_minor=UINT16.unpack_from(
            payload,
            SCHEMA_MINOR_OFFSET,
        )[0],

        exchange_time_ms=UINT64.unpack_from(
            payload,
            EXCHANGE_TIME_OFFSET,
        )[0],

        local_time_ms=UINT64.unpack_from(
            payload,
            LOCAL_TIME_OFFSET,
        )[0],

        monotonic_counter=UINT64.unpack_from(
            payload,
            MONOTONIC_COUNTER_OFFSET,
        )[0],

        producer=_cstring(
            payload[
                PRODUCER_OFFSET:
                PRODUCER_OFFSET + PRODUCER_SIZE
            ]
        ),

        session_id=_cstring(
            payload[
                SESSION_ID_OFFSET:
                SESSION_ID_OFFSET + SESSION_ID_SIZE
            ]
        ),

        symbol=_cstring(
            payload[
                SYMBOL_OFFSET:
                SYMBOL_OFFSET + SYMBOL_SIZE
            ]
        ),

        parent_id_1=_cstring(
            payload[
                PARENT1_OFFSET:
                PARENT1_OFFSET + PARENT1_SIZE
            ]
        ),

        parent_id_2=_cstring(
            payload[
                PARENT2_OFFSET:
                PARENT2_OFFSET + PARENT2_SIZE
            ]
        ),

        algorithm=_cstring(
            payload[
                ALGORITHM_OFFSET:
                ALGORITHM_OFFSET + ALGORITHM_SIZE
            ]
        ),

        algorithm_version=_cstring(
            payload[
                ALGO_VERSION_OFFSET:
                ALGO_VERSION_OFFSET + ALGO_VERSION_SIZE
            ]
        ),

        checksum=UINT32.unpack_from(
            payload,
            CHECKSUM_OFFSET,
        )[0],
    )


# ============================================================
# TickObserved Decoder
# ============================================================

def decode_tick(payload: bytes) -> TickObserved:

    if len(payload) != TICK_OBSERVED_SIZE:
        raise ValueError(
            f"Expected {TICK_OBSERVED_SIZE} bytes "
            f"got {len(payload)}"
        )

    meta = decode_metadata(payload)

    return TickObserved(

        meta=meta,

        bid=DOUBLE.unpack_from(
            payload,
            BID_OFFSET,
        )[0],

        ask=DOUBLE.unpack_from(
            payload,
            ASK_OFFSET,
        )[0],

        last=DOUBLE.unpack_from(
            payload,
            LAST_OFFSET,
        )[0],

        volume_real=DOUBLE.unpack_from(
            payload,
            VOLUME_REAL_OFFSET,
        )[0],

        volume_tick=UINT64.unpack_from(
            payload,
            VOLUME_TICK_OFFSET,
        )[0],

        flags=UINT32.unpack_from(
            payload,
            FLAGS_OFFSET,
        )[0],
    )
