from datetime import datetime
import struct
from eos.layout import *

def read_cstring(data: bytes, offset: int, length: int) -> str:
    return (
        data[offset:offset + length]
        .split(b"\x00")[0]
        .decode("utf-8", errors="ignore")
    )


def decode_metadata(packet: bytes):

    return {

        "event_id":
            read_cstring(packet, OFFSET_EVENT_ID, LEN_EVENT_ID),

        "event_type":
            struct.unpack_from("<H", packet, OFFSET_EVENT_TYPE)[0],

        "domain":
            struct.unpack_from("<H", packet, OFFSET_DOMAIN)[0],

        "schema_major":
            struct.unpack_from("<H", packet, OFFSET_SCHEMA_MAJOR)[0],

        "schema_minor":
            struct.unpack_from("<H", packet, OFFSET_SCHEMA_MINOR)[0],

        "exchange_time":
            struct.unpack_from("<Q", packet, OFFSET_EXCHANGE_TIME)[0],

        "local_time":
            struct.unpack_from("<Q", packet, OFFSET_LOCAL_TIME)[0],

        "symbol":
            read_cstring(packet, OFFSET_SYMBOL, LEN_SYMBOL),

        "producer":
            read_cstring(packet, OFFSET_PRODUCER, LEN_PRODUCER),

        "session":
            read_cstring(packet, OFFSET_SESSION, LEN_SESSION),
    }
