#!/usr/bin/env python3
"""BIOScope protocol bridge with physical USB serial deliberately fail-closed.

The newline JSON session is testable with mock transports. The current
M5Stick runs Bruce and Linux cdc_acm opens assert DTR/RTS; therefore the
physical opener is disabled and this program cannot reset or replace Bruce.
"""
import argparse
import logging
import time
from pathlib import Path

from device_discovery import BY_ID, PROFILES, discover
from m5stick import M5StickAdapter
from serial_protocol import FrameError, JsonLineDecoder, encode

LOG = logging.getLogger('bioscope.m5stick')
PROTOCOL_VERSION = 1
EXPECTED_VID = 0x1A86
EXPECTED_PID = 0x55D4


class PortIdentityError(RuntimeError):
    pass


class PhysicalSerialDisabled(RuntimeError):
    pass


def verify_target(port, expected_serial, ports_module=None, inventory=None, by_id_dir=BY_ID):
    """Read-only identity preflight; never opens the selected tty."""
    profile = next(p for p in PROFILES if p['id'] == 'm5stick')
    expected_port = str(Path(by_id_dir) / profile['expected_by_id'])
    if str(port) != expected_port or expected_serial != profile['serial']:
        raise PortIdentityError('port and expected serial must match the configured M5Stick persistent profile')
    devices = discover(by_id_dir=by_id_dir) if inventory is None else inventory
    device = next((d for d in devices if d['id'] == 'm5stick'), None)
    if not device or not device['connected'] or not device.get('serial_link_available'):
        raise PortIdentityError('M5Stick USB descriptors, topology, or persistent serial path do not fully match')
    if device.get('persistent_port') != expected_port or device.get('serial') != expected_serial:
        raise PortIdentityError('M5Stick profile changed during preflight')

    if ports_module is None:
        from serial.tools import list_ports
        ports_module = list_ports
    resolved = str(Path(expected_port).resolve(strict=True))
    info = next((item for item in ports_module.comports() if str(Path(item.device).resolve()) == resolved), None)
    if info is None:
        raise PortIdentityError('persistent link has no matching pyserial USB inventory record')
    if (info.vid, info.pid, info.serial_number) != (EXPECTED_VID, EXPECTED_PID, expected_serial):
        raise PortIdentityError('pyserial USB descriptor check failed; port left unopened')
    return info


class ProtocolSession:
    """Versioned, bounded, catalog-only protocol logic independent of tty IO."""
    def __init__(self, handler=None):
        self.decoder = JsonLineDecoder()
        self.handler = handler or M5StickAdapter()
        self.hello_seen = False

    def feed(self, data):
        responses = []
        try:
            messages = self.decoder.feed(data)
        except FrameError as error:
            LOG.warning('Rejected malformed M5Stick frame: %s', error)
            return [encode({'type': 'error', 'protocol': PROTOCOL_VERSION, 'message': 'malformed protocol frame'})]
        for message in messages:
            if not self.hello_seen:
                if message.get('type') != 'hello':
                    LOG.warning('Rejected message before protocol hello')
                    responses.append(encode({'type': 'error', 'protocol': PROTOCOL_VERSION, 'message': 'hello required'}))
                    continue
                self.hello_seen = True
            for response in self.handler.handle(message):
                responses.append(encode(response))
        return responses


def serve_transport(transport, timeout_seconds=30, monotonic=time.monotonic):
    """Run the protocol over a mock/test transport; return on EOF or timeout."""
    session = ProtocolSession()
    last_data = monotonic()
    while True:
        try:
            raw = transport.readline()
        except (OSError, EOFError) as error:
            LOG.info('M5Stick transport disconnected: %s', error)
            return 'DISCONNECTED'
        if raw:
            last_data = monotonic()
            for response in session.feed(raw):
                transport.write(response)
        elif monotonic() - last_data >= timeout_seconds:
            LOG.info('M5Stick protocol idle timeout')
            return 'TIMEOUT'


def run(port, expected_serial, serial_module=None, ports_module=None, inventory=None, by_id_dir=BY_ID):
    """Verify the identity, then stop before any unsafe CDC ACM open."""
    verify_target(port, expected_serial, ports_module=ports_module, inventory=inventory, by_id_dir=by_id_dir)
    raise PhysicalSerialDisabled(
        'physical M5Stick serial is disabled: this target uses Linux cdc_acm; '
        'TTY open raises DTR/RTS and the prepared Bruce/BIOScope protocols differ'
    )


def main():
    parser = argparse.ArgumentParser(description='BIOScope M5Stick bridge safety preflight; physical serial is disabled')
    parser.add_argument('--port', required=True, help='exact configured /dev/serial/by-id path')
    parser.add_argument('--expected-serial', required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    try:
        verify_target(args.port, args.expected_serial)
        print('USB profile verified; port remains unopened. Physical serial is disabled pending reset-free protocol verification.')
        return 0
    except Exception as error:
        LOG.error('%s', error)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
