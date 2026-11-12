import unittest
import importlib.util
from pathlib import Path

from dabao_hardware import HardwareRun, HardwareState, capabilities, prepare_execution_request

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/dabao-readonly-version.py"
SPEC = importlib.util.spec_from_file_location("dabao_readonly_version", SCRIPT)
VERSION_QUERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERSION_QUERY)


class DabaoHardwarePlanningTests(unittest.TestCase):
    def setUp(self):
        self.device = {
            "id": "dabao", "connected": True, "vid": "1d50", "pid": "6197",
            "serial": "TLZ4A6", "usb_topology": "1-4", "observed_product": "Dabao",
            "serial_link_available": True,
            "persistent_port": "/dev/serial/by-id/usb-Baochip_Dabao_TLZ4A6-if02",
        }

    def test_capability_reports_recorded_hardware_run_but_execution_remains_disabled(self):
        report = capabilities([self.device])
        self.assertTrue(report["identity_verified"])
        self.assertEqual(report["execution_state"], HardwareState.CAPABILITY_CHECK.value)
        self.assertFalse(report["physical_execution_enabled"])
        self.assertEqual(report["hardware_firmware"], "Xous v0.10.1-43-g8964027ff (run evidence)")
        self.assertEqual(report["last_verified_run"]["actual"], "0xB105C0DE")
        self.assertIn("one-shot probe is consumed", report["reason"])

    def test_request_lists_side_effects_without_opening_or_executing(self):
        request = prepare_execution_request("dabao-fifo-probe", [self.device])
        self.assertEqual(request["state"], HardwareState.CAPABILITY_CHECK.value)
        self.assertEqual(request["evidence"], "NOT RUN")
        self.assertTrue(any("keystore" in item for item in request["side_effects"]))
        self.assertIn("ver xous", request["required_preflight_after_operator_approval"][0])
        self.assertTrue(request["physical_write_approval_required"])
        self.assertEqual(request["target"]["serial"], "TLZ4A6")

    def test_wrong_usb_identity_is_rejected(self):
        other = {**self.device, "serial": "NOT-THE-BOARD"}
        with self.assertRaisesRegex(RuntimeError, "identity"):
            prepare_execution_request("dabao-fifo-probe", [other])

    def test_non_catalog_experiment_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "allow-listed"):
            prepare_execution_request("arbitrary-command", [self.device])

    def test_hardware_verified_requires_captured_matching_target_response(self):
        run = HardwareRun("dabao-fifo-probe", expected_observation="0xb105c0de")
        run.transition(HardwareState.CAPABILITY_CHECK)
        run.transition(HardwareState.VALIDATING)
        run.transition(HardwareState.AWAITING_APPROVAL)
        run.transition(HardwareState.READY)
        run.transition(HardwareState.EXECUTING)
        with self.assertRaisesRegex(ValueError, "actual target response"):
            run.transition(HardwareState.RESULT_CAPTURED)
        run.captured_observation = "0xb105c0de"
        run.transition(HardwareState.RESULT_CAPTURED)
        self.assertEqual(run.evidence, "HARDWARE_EXECUTED")
        run.transition(HardwareState.HARDWARE_VERIFIED)
        self.assertEqual(run.evidence, "HARDWARE_VERIFIED")

    def test_unexpected_state_jump_is_rejected(self):
        run = HardwareRun("dabao-fifo-probe")
        with self.assertRaisesRegex(ValueError, "invalid hardware run transition"):
            run.transition(HardwareState.HARDWARE_VERIFIED)

    def test_readonly_version_query_sends_only_one_fixed_command_and_closes(self):
        class FakeSerial:
            EIGHTBITS, PARITY_NONE, STOPBITS_ONE = 8, "N", 1
            instance = None
            def __init__(self, **kwargs):
                self.kwargs = kwargs; self.writes = []; self.closed = False
                self.responses = [b"Xous version: test-build\r\n"]
                FakeSerial.instance = self
            def open(self): self.opened = True
            def write(self, data): self.writes.append(data); return len(data)
            def readline(self): return self.responses.pop(0) if self.responses else b""
            def close(self): self.closed = True
        class FakeModule:
            Serial = FakeSerial
            EIGHTBITS, PARITY_NONE, STOPBITS_ONE = 8, "N", 1
        ticks = [0]
        def monotonic():
            ticks[0] += 1
            return float(ticks[0])
        result = VERSION_QUERY.query_version(FakeModule, lambda: "/dev/fake-by-id", monotonic)
        serial = FakeSerial.instance
        self.assertEqual(serial.writes, [b"ver xous\r\n"])
        self.assertEqual(result["response"], "Xous version: test-build")
        self.assertTrue(serial.closed)
        self.assertTrue(serial.kwargs["exclusive"])
        self.assertFalse(serial.dtr)
        self.assertFalse(serial.rts)

    def test_version_query_cli_requires_possible_reset_acknowledgment(self):
        with self.assertRaises(SystemExit) as error:
            VERSION_QUERY.main([])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
