import json
import tempfile
import unittest
from pathlib import Path

from dabao_pulselink import TARGET, make_chunk, stage_pulselink, verify_build


class FakeConnection:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.commands = []
        self.responses = []
        self.opened = False
        self.closed = False
        self.dtr = True
        self.rts = True
        self.port = None

    def open(self): self.opened = True
    def close(self): self.closed = True
    def write(self, data):
        line = data.decode().strip()
        self.commands.append(line)
        response = "SUCCESS" if line == "bio pad" else "OK"
        self.responses.append(("[console] " + response + "\r\n").encode())
        return len(data)
    def readline(self): return self.responses.pop(0) if self.responses else b""


class FakeSerialModule:
    EIGHTBITS = 8
    PARITY_NONE = "N"
    STOPBITS_ONE = 1
    def __init__(self): self.instances = []
    def Serial(self, **kwargs):
        value = FakeConnection(**kwargs)
        self.instances.append(value)
        return value


def exact_device():
    return {"id":"dabao", "connected":True, "serial_link_available":True, "serial_opened":False,
            "vid":TARGET["vid"], "pid":TARGET["pid"], "observed_product":TARGET["product"],
            "serial":TARGET["serial"], "usb_topology":TARGET["topology"], "persistent_port":TARGET["port"]}


class DabaoPulseLinkStagingTests(unittest.TestCase):
    def test_exact_58_byte_build_and_loader_chunk(self):
        image, manifest = verify_build()
        chunk = make_chunk(image)
        self.assertEqual(len(image), 58)
        self.assertEqual(len(chunk), 70)
        self.assertEqual(chunk[:2], b"\0\0")
        self.assertEqual(chunk[2:60], image)
        self.assertEqual(chunk[60:66], b"\0"*6)
        self.assertEqual(int.from_bytes(chunk[-4:], "big"), __import__("zlib").crc32(chunk[:-4]))
        self.assertEqual(manifest["timing"]["requested_quantum_hz"], 7000)

    def test_stage_config_and_program_but_never_reload(self):
        fake = FakeSerialModule()
        with tempfile.TemporaryDirectory() as temp:
            manifest = stage_pulselink(serial_module=fake, discovery=lambda: [exact_device()], run_root=Path(temp))
            self.assertEqual(manifest["state"], "PROGRAM_STAGED_NOT_RELOADED")
            self.assertTrue(manifest["commit_response_verified"])
            self.assertFalse(manifest["reload_sent"])
            self.assertFalse(manifest["execution_started_by_this_run"])
            conn = fake.instances[0]
            self.assertTrue(conn.opened and conn.closed)
            self.assertFalse(conn.dtr or conn.rts)
            self.assertEqual(conn.commands[0:2], ["bio pin 1", "bio clk 7000"])
            self.assertTrue(conn.commands[2].startswith("bio "))
            self.assertTrue(conn.commands[2].endswith("=="))
            self.assertEqual(conn.commands[3], "bio pad")
            self.assertFalse(any("reload" in command or "clear" in command for command in conn.commands))
            saved = json.loads((Path(temp) / manifest["run_id"] / "manifest.json").read_text())
            self.assertEqual(saved["evidence"], "TARGET_PROGRAM_STAGED")

    def test_wrong_device_is_rejected_before_serial_open(self):
        fake = FakeSerialModule()
        wrong = exact_device(); wrong["serial"] = "WRONG"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "identity/path mismatch"):
                stage_pulselink(serial_module=fake, discovery=lambda: [wrong], run_root=Path(temp))
        self.assertEqual(fake.instances, [])


if __name__ == "__main__": unittest.main()
