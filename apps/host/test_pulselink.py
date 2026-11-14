import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from pulselink import PulseLinkStore, TelemetryError, parse_telemetry


def frame(sequence=0, state="waiting", pulse_count=0, frequency=None, level=0, uptime=1_000_000, edges=None, **extra):
    value = {"protocol":1,"device":"m5stick-pulse-link","type":"telemetry","sequence":sequence,
             "state":state,"pulse_count":pulse_count,"frequency_hz":frequency,"signal_level":level,
             "uptime_us":uptime,"edge_overflow":False,"edges":edges or []}
    value.update(extra)
    return json.dumps(value)


class PulseLinkTelemetryTests(unittest.TestCase):
    def test_waiting_and_actual_measurement_parse(self):
        waiting = parse_telemetry(frame())
        self.assertIsNone(waiting["frequency_hz"])
        measured = parse_telemetry(frame(sequence=2,state="measuring",pulse_count=2,frequency=1.001,level=0))
        self.assertAlmostEqual(measured["frequency_hz"], 1.001)

    def test_rejects_malformed_json_unknown_fields_wrong_protocol_and_invalid_values(self):
        for bad in ("{oops", frame(extra=True), frame(protocol=2), frame(pulse_count=11),
                    frame(frequency=float("nan")), frame(level=2), frame(edges=[{"timestamp_us":1}])):
            with self.subTest(bad=bad), self.assertRaises(TelemetryError): parse_telemetry(bad)
        with self.assertRaises(TelemetryError): parse_telemetry(b"x" * 2049)

    def test_frequency_and_edges_are_not_synthesized_when_missing(self):
        data = parse_telemetry(frame())
        self.assertEqual(data["edges"], [])
        self.assertIsNone(data["frequency_hz"])

    def test_disconnect_staleness_and_reconnect(self):
        store = PulseLinkStore()
        now = datetime.now(timezone.utc)
        store.ingest(frame(), now=now)
        self.assertTrue(store.snapshot(now=now.timestamp())["connected"])
        self.assertFalse(store.snapshot(now=now.timestamp()+3)["connected"])
        store.disconnect("test disconnect")
        self.assertFalse(store.snapshot()["connected"])
        store.ingest(frame(sequence=1, uptime=1_100_000), now=now+timedelta(seconds=4))
        self.assertTrue(store.snapshot()["connected"])

    def test_out_of_order_frames_rejected(self):
        store = PulseLinkStore()
        store.ingest(frame(sequence=4))
        with self.assertRaises(TelemetryError): store.ingest(frame(sequence=4, uptime=1_100_000))

    def test_genuine_edge_sequence_creates_vcd_only_after_complete_ten_pulses(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture_root = root / "artifacts/runs"
            with patch("pulselink.ROOT", root):
                store = PulseLinkStore(capture_root=capture_root)
                store.ingest(frame(), now=datetime.now(timezone.utc))
                for index in range(1, 21):
                    level = index % 2
                    count = (index + 1) // 2
                    complete = index == 20
                    payload = frame(sequence=index, state="complete" if complete else "measuring",
                                    pulse_count=count, frequency=1.0 if count >= 2 else None,
                                    level=level, uptime=1_000_000 + index*500_000,
                                    edges=[{"timestamp_us":(1_000_000 + index*500_000) & 0xFFFFFFFF,"level":level}])
                    store.ingest(payload, now=datetime.now(timezone.utc))
                status = store.snapshot()
                self.assertTrue(status["capture_complete"])
                self.assertEqual(status["capture"]["evidence"], "LIVE_HARDWARE")
                trace = root / status["capture"]["path"]
                content = trace.read_text()
                self.assertIn("$timescale 1 us $end", content)
                self.assertEqual(content.count("!\n"), 21)
                manifest = json.loads((trace.parent / "manifest.json").read_text())
                self.assertEqual(manifest["evidence"], "LIVE_HARDWARE")

    def test_incomplete_or_overflowed_edges_never_make_a_complete_capture(self):
        store = PulseLinkStore()
        store.ingest(frame())
        for index in range(1, 21):
            count = (index + 1) // 2
            store.ingest(frame(sequence=index, state="complete" if index == 20 else "measuring",
                               pulse_count=count, frequency=1.0 if count >= 2 else None,
                               level=index % 2, uptime=1_000_000+index*500_000,
                               edges=[{"timestamp_us":(1_000_000+index*500_000)&0xffffffff,"level":index%2}],
                               edge_overflow=index == 5))
        self.assertFalse(store.snapshot()["capture_complete"])
        self.assertIsNone(store.snapshot()["capture"])


if __name__ == "__main__": unittest.main()
