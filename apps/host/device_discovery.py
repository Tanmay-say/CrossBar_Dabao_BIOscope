"""Read-only, identity-correlated USB serial discovery for BIOScope.

Only sysfs and /dev/serial/by-id are read. This module never opens tty devices.
Profiles combine VID/PID, USB serial and the observed physical USB topology;
VID/PID alone is deliberately insufficient to identify either board.
"""
from pathlib import Path
from datetime import datetime, timezone

SYS_USB = Path('/sys/bus/usb/devices')
BY_ID = Path('/dev/serial/by-id')
_DEVICE_HISTORY = {}

# M5Stick association was physically corroborated by the operator and USB add
# event. USB itself exposes the CH9102 bridge identity, not the M5Stack model.
PROFILES = (
    {
        'id': 'dabao', 'name': 'Baochip-1x Dabao', 'vid': '1d50', 'pid': '6196',
        'serial': 'TLZ4A6', 'topology': '1-4', 'vendor': 'OpenMoko, Inc.',
        'product': 'Baochip-1x', 'identity_basis': 'USB descriptors + serial + topology',
        'confidence': 'high', 'safety': 'CDC console may accept update-capable commands; unopened',
        'expected_by_id': 'usb-Baochip_Baochip-1x_TLZ4A6-if00',
    },
    {
        'id': 'm5stick', 'name': 'M5StickC Plus2 (operator-correlated)', 'vid': '1a86', 'pid': '55d4',
        'serial': '5B1E046678', 'topology': '1-3', 'vendor': 'QinHeng Electronics',
        'product': 'USB Single Serial', 'identity_basis': 'operator-reported board + USB arrival, serial + topology',
        'confidence': 'high association; bridge descriptors only',
        'safety': 'Bruce firmware preserved; serial protocol not connected',
        'expected_by_id': 'usb-1a86_USB_Single_Serial_5B1E046678-if00',
    },
)


def _read(path):
    try:
        return path.read_text().strip()
    except (OSError, UnicodeError):
        return None


def _port_for(serial, by_id_dir):
    for link in sorted(by_id_dir.glob('*')):
        # The serial is part of the generated systemd by-id name and also
        # checked by exact expected-link equality in the caller.
        if serial in link.name:
            try:
                target = link.resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if target.name.startswith(('ttyACM', 'ttyUSB')):
                return str(link), str(target)
    return None, None


def _interfaces(device):
    result = []
    for interface in sorted(device.parent.glob(device.name + ':*')):
        number = _read(interface / 'bInterfaceNumber')
        driver = None
        try:
            driver = (interface / 'driver').resolve(strict=True).name
        except (OSError, RuntimeError):
            pass
        if number is not None or driver is not None:
            result.append({'number': number, 'driver': driver})
    return result


def discover(sys_usb=SYS_USB, by_id_dir=BY_ID, history=None, now=None):
    """Return two stable profile records with live, read-only link state."""
    if history is None:
        history = _DEVICE_HISTORY
    observed_at = now or datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    observed = {}
    for dev in sys_usb.iterdir() if sys_usb.exists() else ():
        # Ignore interface, hub and non-device entries lacking USB descriptors.
        vid, pid = _read(dev / 'idVendor'), _read(dev / 'idProduct')
        serial = _read(dev / 'serial')
        if vid is not None and pid is not None:
            observed[(vid.lower(), pid.lower(), serial, dev.name)] = dev

    results = []
    for profile in PROFILES:
        item = dict(profile)
        exact_key = (profile['vid'], profile['pid'], profile['serial'], profile['topology'])
        dev = observed.get(exact_key)
        by_id_path, tty_path = _port_for(profile['serial'], by_id_dir)
        # Require the persistent link to match the selected board profile and
        # resolve to the kernel's tty. A stale/mismatched link is never trusted.
        if by_id_path and Path(by_id_path).name != profile['expected_by_id']:
            by_id_path, tty_path = None, None
        # Physical USB presence is based on the complete hardware profile in
        # sysfs. Serial availability is a separate signal (important when the
        # host process is sandboxed away from /dev).
        connected = bool(dev)
        serial_available = bool(by_id_path and tty_path and Path(tty_path).exists())
        previous = history.get(profile['id'], {})
        changed_at = previous.get('last_connection_change_at')
        if previous.get('connected') != connected:
            changed_at = observed_at if connected or previous else None
        last_verified = observed_at if connected else previous.get('last_verified_at')
        if connected or previous:
            history[profile['id']] = {
                'connected': connected,
                'last_connection_change_at': changed_at,
                'last_verified_at': last_verified,
            }
        item.update({
            'connected': connected,
            'usb_present': connected,
            'serial_link_available': serial_available,
            'usb_topology': profile['topology'] if dev else None,
            'manufacturer_descriptor': _read(dev / 'manufacturer') if dev else None,
            'interfaces': _interfaces(dev) if dev else [],
            'persistent_port': by_id_path if serial_available else None,
            'linux_device': tty_path if serial_available else None,
            'status': ('USB identity profile matched; serial link available, unopened' if serial_available else
                       'USB identity profile matched; serial link unavailable to host process' if connected else
                       'USB profile not present or did not fully match'),
            'connection_event': 'connected' if connected else 'disconnected',
            'last_connection_change_at': changed_at,
            'last_verified_at': last_verified,
            'serial_opened': False,
        })
        results.append(item)
    return results
