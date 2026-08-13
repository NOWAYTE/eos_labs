import asyncio
import struct
import tempfile
import unittest
from pathlib import Path

from engines.market_state_engine import MarketStateEngine
from event_bus import EventBus
from models import EventMetadata, TickObserved
from replay import Replay


def decoded_tick(payload: bytes) -> TickObserved:
    sequence = payload[0]
    return TickObserved(
        meta=EventMetadata(
            event_id=str(sequence), event_type=0, domain=0,
            schema_major=1, schema_minor=0,
            exchange_time_ms=sequence * 1_000,
            local_time_ms=sequence * 1_000, monotonic_counter=sequence,
            producer="test", session_id="", symbol="EURUSD",
            parent_id_1="", parent_id_2="", algorithm="",
            algorithm_version="", checksum=0,
        ),
        bid=float(sequence), ask=float(sequence + 2), last=0.0,
        volume_real=0.0, volume_tick=0, flags=0,
    )


class ReplayTests(unittest.IsolatedAsyncioTestCase):
    async def test_replay_publishes_framed_payloads_to_the_bus(self):
        payloads = [b"first", b"second"]
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "ticks.bin"
            with filename.open("wb") as stream:
                for payload in payloads:
                    stream.write(struct.pack("<I", len(payload)))
                    stream.write(payload)

            bus = EventBus()
            received = []
            bus.subscribe(bytes, lambda event: received.append(event))
            await bus.start()
            try:
                replay = Replay(filename, decoder=lambda payload: payload)
                count = await replay.publish(bus)
                await bus.join()
            finally:
                await bus.stop()

        self.assertEqual(count, 2)
        self.assertEqual(received, payloads)

    async def test_replay_rebuilds_the_same_market_state_as_direct_events(self):
        payloads = [bytes([1]), bytes([2]), bytes([4])]
        direct_engine = MarketStateEngine(window_size=2)
        for payload in payloads:
            direct_engine.on_tick(decoded_tick(payload))

        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "ticks.bin"
            with filename.open("wb") as stream:
                for payload in payloads:
                    stream.write(struct.pack("<I", len(payload)))
                    stream.write(payload)

            replay_engine = MarketStateEngine(window_size=2)
            bus = EventBus()
            bus.subscribe(TickObserved, replay_engine.on_tick)
            await bus.start()
            try:
                await Replay(filename, decoder=decoded_tick).publish(bus)
                await bus.join()
            finally:
                await bus.stop()

        self.assertEqual(
            replay_engine.get("EURUSD"),
            direct_engine.get("EURUSD"),
        )
