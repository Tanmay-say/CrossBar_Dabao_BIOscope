import json
import base64
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from bio_sim import ROOT, run_experiment
from dabao_adapter import (APPROVAL_PHRASE, BIO_BINARY, BIO_SOURCE, CHUNK_WIRE_BYTES,
                           EXPECTED_WORD, _verify_binary, make_chunk, run_fifo_probe)


class FakeConnection:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._port = None
        self.dtr = True
        self.rts = True
        self.is_open = False
        self.closed = False
        self.writes = []
        self.lines = []

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    def open(self):
        self.is_open = True

    def write(self, data):
        self.writes.append(data)
        if data.startswith(b"bio rx"):
            self.lines.extend([b"INFO: 0xb105c0de\r\n", b"OK\r\n"])
        elif data == b"bio pad\n":
            self.lines.append(b"SUCCESS\r\n")
        elif data == b"bio reload\n":
            self.lines.append(b"BIO load successful\r\n")
        elif data.startswith(b"bio ") and data != b"bio ready\n":
            base64.b64decode(data[4:].strip())
            self.lines.append(b"OK\r\n")
        else:
            self.lines.append(b"OK\r\n")

    def readline(self):
        return self.lines.pop(0) if self.lines else b""

    def close(self):
        self.closed = True
        self.is_open = False


class FakeSerial:
    EIGHTBITS, PARITY_NONE, STOPBITS_ONE = 8, "N", 1

    def __init__(self):
        self.connection = None

    def Serial(self, **kwargs):
        self.connection = FakeConnection(**kwargs)
        return self.connection


def matching_device():
    return [{"id": "dabao", "connected": True, "vid": "1d50", "pid": "6197",
             "observed_product": "Dabao", "serial": "TLZ4A6", "usb_topology": "1-4",
             "persistent_port": "/dev/serial/by-id/usb-Baochip_Dabao_TLZ4A6-if02",
             "serial_link_available": True, "serial_opened": False, "linux_device": "/dev/ttyACM0"}]


class DabaoUploaderProtocolTests(unittest.TestCase):
    @unittest.skipUnless(BIO_BINARY.is_file(), "run scripts/build-dabao-bio-probe.py to produce the local binary")
    def test_build_image_matches_pinned_manifest_and_chunk_wire_format(self):
        manifest, image = _verify_binary()
        self.assertEqual(len(image), 20)
        self.assertIn("0xB105C0DE", manifest["program_effect"])
        wire = make_chunk(0, image)
        self.assertEqual(len(wire), CHUNK_WIRE_BYTES)
        self.assertEqual(int.from_bytes(wire[:2], "big"), 0)
        self.assertEqual(wire[2:22], image)
        self.assertEqual(wire[22:66], bytes(44))
        import zlib
        self.assertEqual(int.from_bytes(wire[66:], "big"), zlib.crc32(wire[:66]) & 0xffffffff)

    def test_wrong_approval_does_not_discover_or_open_port(self):
        serial = FakeSerial()
        with self.assertRaises(PermissionError):
            run_fifo_probe("no", serial_module=serial, discovery_fn=lambda: self.fail("discovery must not run"))
        self.assertIsNone(serial.connection)

    def test_wrong_identity_does_not_open_port(self):
        serial = FakeSerial()
        devices = matching_device()
        devices[0]["serial"] = "OTHER"
        with tempfile.TemporaryDirectory() as temp, patch("dabao_adapter.PUBLIC_EVIDENCE_MANIFEST", Path(temp) / "no-public-record"), self.assertRaises(Exception):
            run_fifo_probe(APPROVAL_PHRASE, serial_module=serial, discovery_fn=lambda: devices,
                           runs_dir=Path(temp))
        self.assertIsNone(serial.connection)

    def test_recorded_physical_attempt_cannot_be_retried(self):
        serial = FakeSerial()
        with tempfile.TemporaryDirectory() as temp, patch("dabao_adapter.PUBLIC_EVIDENCE_MANIFEST", Path(temp) / "no-public-record"):
            prior = Path(temp) / "prior"; prior.mkdir()
            (prior / "manifest.json").write_text(json.dumps({
                "experiment_id": "dabao-fifo-probe", "mode": "HARDWARE", "state": "FAILED"
            }))
            with self.assertRaisesRegex(PermissionError, "refusing to retry"):
                run_fifo_probe(APPROVAL_PHRASE, serial_module=serial,
                               discovery_fn=lambda: self.fail("must stop before USB discovery"),
                               runs_dir=Path(temp))
        self.assertIsNone(serial.connection)

    def test_published_hardware_evidence_consumes_probe_gate(self):
        serial = FakeSerial()
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "public-manifest.json"
            evidence.write_text(json.dumps({
                "experiment_id": "dabao-fifo-probe", "mode": "HARDWARE",
                "evidence": "HARDWARE_VERIFIED",
            }))
            with patch("dabao_adapter.PUBLIC_EVIDENCE_MANIFEST", evidence), self.assertRaisesRegex(PermissionError, "refusing to retry"):
                run_fifo_probe(APPROVAL_PHRASE, serial_module=serial,
                               discovery_fn=lambda: self.fail("must stop before USB discovery"),
                               runs_dir=Path(temp) / "empty-runs")
        self.assertIsNone(serial.connection)

    @unittest.skipUnless(BIO_BINARY.is_file(), "run scripts/build-dabao-bio-probe.py to produce the local binary")
    def test_approved_protocol_reads_one_fifo_word_and_closes(self):
        serial = FakeSerial()
        with tempfile.TemporaryDirectory() as temp, patch("dabao_adapter.PUBLIC_EVIDENCE_MANIFEST", Path(temp) / "no-public-record"):
            manifest = run_fifo_probe(APPROVAL_PHRASE, serial_module=serial,
                                      discovery_fn=matching_device, runs_dir=Path(temp))
            connection = serial.connection
            self.assertEqual(manifest["evidence"], "HARDWARE_VERIFIED")
            self.assertEqual(manifest["actual_result"]["value"], "0xB105C0DE")
            self.assertTrue(connection.closed)
            self.assertTrue(connection.kwargs["exclusive"])
            self.assertFalse(connection.dtr)
            self.assertFalse(connection.rts)
            self.assertEqual(len(connection.writes), 5)
            self.assertEqual(connection.writes[0], b"bio ready\n")
            self.assertEqual(connection.writes[2], b"bio pad\n")
            self.assertEqual(connection.writes[3], b"bio reload\n")
            self.assertEqual(connection.writes[4], b"bio rx 1 5\n")
            self.assertTrue((Path(temp) / manifest["run_id"] / "hardware-result.json").is_file())

    @unittest.skipUnless(BIO_BINARY.is_file(), "run scripts/build-dabao-bio-probe.py to produce the local binary")
    def test_timeout_closes_port_and_never_retries_fifo_read(self):
        serial = FakeSerial()
        connection = None
        original_factory = serial.Serial
        def silent_factory(**kwargs):
            nonlocal connection
            connection = original_factory(**kwargs)
            # Suppress the FIFO response only; prior protocol acknowledgments remain.
            connection.write = lambda data: connection.writes.append(data) or connection.lines.extend(
                [b"OK\n"] if data == b"bio ready\n" else
                [b"OK\n"] if data.startswith(b"bio ") and data not in (b"bio pad\n", b"bio reload\n") else
                [b"SUCCESS\n"] if data == b"bio pad\n" else
                [b"BIO load successful\n"] if data == b"bio reload\n" else [])
            return connection
        serial.Serial = silent_factory
        ticks = [0.0]
        def fast_monotonic():
            ticks[0] += 1.0
            return ticks[0]
        with tempfile.TemporaryDirectory() as temp, patch("dabao_adapter.PUBLIC_EVIDENCE_MANIFEST", Path(temp) / "no-public-record"), self.assertRaises(RuntimeError):
            run_fifo_probe(APPROVAL_PHRASE, serial_module=serial, discovery_fn=matching_device,
                           runs_dir=Path(temp), monotonic=fast_monotonic)
        self.assertTrue(connection.closed)
        self.assertEqual(connection.writes.count(b"bio rx 1 5\n"), 1)


class DabaoFifoProbeSimulationTests(unittest.TestCase):
    def test_published_physical_runner_is_permanently_locked(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/run-dabao-fifo-probe.py")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("locked after the verified run", result.stderr)

    def test_compiled_probe_is_pinned_errata_checked_and_pin_free(self):
        source = ROOT / "experiments/bio/dabao_fifo_probe/main.c"
        manifest_path = ROOT / "artifacts/builds/dabao_fifo_probe/manifest.json"
        binary = ROOT / "artifacts/builds/dabao_fifo_probe/dabao_fifo_probe.bin"
        self.assertTrue(source.is_file())
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["evidence"], "COMPILE_ONLY")
        self.assertEqual(manifest["binary_size_bytes"], 20)
        self.assertEqual(manifest["binary_sha256"], "cfc0502faf630bae4088e06131f23594d1b14928549743eb774d396b88e6b69b")
        self.assertIn("PASS", manifest["errata_validation"])
        self.assertEqual(manifest["hardware_execution"], "NOT RUN")
        if binary.exists():
            import hashlib
            self.assertEqual(binary.stat().st_size, manifest["binary_size_bytes"])
            self.assertEqual(hashlib.sha256(binary.read_bytes()).hexdigest(), manifest["binary_sha256"])
        source_text = source.read_text().lower()
        self.assertNotIn("write_gpio", source_text)
        self.assertNotIn("set_gpio", source_text)

    def test_upstream_simulator_receives_expected_fifo_word_and_writes_fst(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as temp:
            result = run_experiment("dabao-fifo-probe", Path(temp))
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["evidence"], "SIMULATED")
        self.assertTrue(result["validation"]["fifo0_sentinel_received"])
        self.assertTrue(result["validation"]["waveform_present"])
        self.assertIn("0xb105c0de", result["stdout"].lower())
        self.assertEqual(result["configuration"]["values"]["commands"][-1]["cmd"], "fifo_drain")


if __name__ == "__main__":
    unittest.main()
