import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from device_discovery import PROFILES
from serial_protocol import JsonLineDecoder, FrameError, encode, hello_ack
from m5stick import M5StickAdapter
from m5stick_bridge import (
    PhysicalSerialDisabled, PortIdentityError, ProtocolSession, run,
    serve_transport, verify_target,
)


class SerialProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.by_id = root / 'by-id'
        self.by_id.mkdir()
        self.tty = root / 'ttyACM1'
        self.tty.touch()
        self.port = self.by_id / next(p for p in PROFILES if p['id'] == 'm5stick')['expected_by_id']
        self.port.symlink_to(self.tty)
        self.inventory = [{
            'id': 'm5stick', 'connected': True, 'serial_link_available': True,
            'persistent_port': str(self.port), 'serial': '5B1E046678',
        }]

    def tearDown(self):
        self.temp.cleanup()

    def ports(self, vid=0x1A86, pid=0x55D4, serial='5B1E046678'):
        entry = SimpleNamespace(device=str(self.tty), vid=vid, pid=pid, serial_number=serial)
        return SimpleNamespace(comports=lambda: [entry])

    def test_roundtrip_fragmented(self):
        frame = encode({'type': 'hello', 'protocol': 1}); decoder = JsonLineDecoder()
        self.assertEqual(decoder.feed(frame[:3]), [])
        self.assertEqual(decoder.feed(frame[3:]), [{'type': 'hello', 'protocol': 1}])

    def test_multiple_frames(self):
        decoder = JsonLineDecoder()
        self.assertEqual(len(decoder.feed(encode({'type': 'hello', 'protocol': 1}) + encode(hello_ack()))), 2)

    def test_invalid_json(self):
        with self.assertRaises(FrameError): JsonLineDecoder().feed(b'{nope}\n')

    def test_wrong_version(self):
        with self.assertRaises(FrameError): encode({'type': 'hello', 'protocol': 2})

    def test_oversized(self):
        with self.assertRaises(FrameError): JsonLineDecoder().feed(b'x' * 1100)

    def test_host_hello(self):
        self.assertEqual(M5StickAdapter().handle({'type': 'hello', 'protocol': 1})[0]['type'], 'hello_ack')

    def test_host_rejects_hardware_mode(self):
        result = M5StickAdapter().handle({'type': 'run_request', 'protocol': 1, 'experiment_id': 'blink', 'mode': 'HARDWARE'})
        self.assertEqual(result[0]['type'], 'error')

    def test_host_rejects_extra_or_malformed_run_fields(self):
        adapter = M5StickAdapter()
        extra = adapter.handle({'type': 'run_request', 'protocol': 1, 'experiment_id': 'blink', 'mode': 'SIMULATION', 'command': 'arbitrary'})
        malformed = adapter.handle({'type': 'run_request', 'protocol': 1, 'experiment_id': [], 'mode': 'SIMULATION'})
        self.assertEqual(extra[0]['type'], 'error')
        self.assertEqual(malformed[0]['type'], 'error')

    def test_host_executes_catalog_mock_only(self):
        result = M5StickAdapter().handle({'type': 'run_request', 'protocol': 1, 'experiment_id': 'mock-loopback', 'mode': 'MOCK'})
        self.assertEqual(result[-1]['type'], 'run_result')

    def test_identity_preflight_requires_all_descriptors_and_persistent_path(self):
        info = verify_target(str(self.port), '5B1E046678', self.ports(), self.inventory, self.by_id)
        self.assertEqual(info.serial_number, '5B1E046678')

    def test_identity_preflight_rejects_wrong_vid_pid_or_serial(self):
        with self.assertRaises(PortIdentityError):
            verify_target(str(self.port), '5B1E046678', self.ports(vid=0x1234), self.inventory, self.by_id)
        with self.assertRaises(PortIdentityError):
            verify_target(str(self.port), 'wrong', self.ports(), self.inventory, self.by_id)

    def test_identity_preflight_rejects_unknown_topology_profile(self):
        mismatched = [{**self.inventory[0], 'connected': False}]
        with self.assertRaises(PortIdentityError):
            verify_target(str(self.port), '5B1E046678', self.ports(), mismatched, self.by_id)

    def test_physical_open_stays_disabled_after_identity_check(self):
        serial = SimpleNamespace(created=False)
        def make_serial(): serial.created = True; raise AssertionError('must not construct a physical serial transport')
        serial.Serial = make_serial
        with patch('m5stick_bridge.verify_target', return_value=self.ports().comports()[0]):
            with self.assertRaises(PhysicalSerialDisabled):
                run(str(self.port), '5B1E046678', serial, self.ports())
        self.assertFalse(serial.created)

    def test_mock_transport_handshake_and_catalog_request(self):
        class Transport:
            def __init__(self):
                self.incoming = iter([
                    encode({'type': 'hello', 'protocol': 1}),
                    encode({'type': 'run_request', 'protocol': 1, 'experiment_id': 'mock-loopback', 'mode': 'MOCK'}),
                ])
                self.writes = []
            def readline(self):
                try: return next(self.incoming)
                except StopIteration: raise EOFError('mock disconnect')
            def write(self, data): self.writes.append(data)
        transport = Transport()
        self.assertEqual(serve_transport(transport), 'DISCONNECTED')
        decoder = JsonLineDecoder(); replies = []
        for frame in transport.writes: replies.extend(decoder.feed(frame))
        self.assertEqual([r['type'] for r in replies], ['hello_ack', 'run_status', 'run_result'])

    def test_mock_transport_timeout(self):
        ticks = iter([0.0, 0.4, 0.8, 1.2])
        class EmptyTransport:
            def readline(self): return b''
        self.assertEqual(serve_transport(EmptyTransport(), timeout_seconds=1.0, monotonic=lambda: next(ticks)), 'TIMEOUT')

    def test_session_rejects_request_before_hello(self):
        session = ProtocolSession()
        replies = session.feed(encode({'type': 'run_request', 'protocol': 1, 'experiment_id': 'mock-loopback', 'mode': 'MOCK'}))
        message = JsonLineDecoder().feed(replies[0])[0]
        self.assertEqual(message['type'], 'error')
        self.assertFalse(session.hello_seen)


if __name__ == '__main__':
    unittest.main()
