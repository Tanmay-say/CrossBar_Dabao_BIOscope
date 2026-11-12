import tempfile
import unittest
from pathlib import Path

from device_discovery import discover


class DeviceDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.usb = self.root / 'sys' / 'usb'
        self.by_id = self.root / 'dev' / 'serial' / 'by-id'
        self.tty = self.root / 'dev'
        self.usb.mkdir(parents=True)
        self.by_id.mkdir(parents=True)
        self.tty.mkdir(exist_ok=True)

    def tearDown(self):
        self.temp.cleanup()

    def attach(self, topology, vid, pid, serial, product):
        dev = self.usb / topology
        dev.mkdir()
        for key, value in {'idVendor': vid, 'idProduct': pid, 'serial': serial, 'product': product}.items():
            (dev / key).write_text(value)
        iface = self.usb / f'{topology}:{topology[-1]}.0'
        iface.mkdir()
        (iface / 'bInterfaceNumber').write_text('00')
        driver = self.root / 'sys' / 'drivers' / 'cdc_acm'
        driver.mkdir(parents=True, exist_ok=True)
        (iface / 'driver').symlink_to(driver)
        return dev

    def attach_port(self, link_name, tty_name):
        target = self.tty / tty_name
        target.touch()
        (self.by_id / link_name).symlink_to(target)

    def test_matches_profiles_using_usb_identity_serial_and_topology(self):
        self.attach('1-4', '1d50', '6196', 'TLZ4A6', 'Baochip-1x')
        self.attach('1-3', '1a86', '55d4', '5B1E046678', 'USB Single Serial')
        self.attach_port('usb-Baochip_Baochip-1x_TLZ4A6-if00', 'ttyACM0')
        self.attach_port('usb-1a86_USB_Single_Serial_5B1E046678-if00', 'ttyACM1')
        devices = {item['id']: item for item in discover(self.usb, self.by_id)}
        self.assertTrue(devices['dabao']['connected'])
        self.assertTrue(devices['m5stick']['connected'])
        self.assertEqual(devices['dabao']['linux_device'], str(self.tty / 'ttyACM0'))
        self.assertEqual(devices['m5stick']['persistent_port'], str(self.by_id / 'usb-1a86_USB_Single_Serial_5B1E046678-if00'))
        self.assertEqual(devices['m5stick']['interfaces'][0]['driver'], 'cdc_acm')
        self.assertFalse(devices['m5stick']['serial_opened'])

    def test_matches_current_dabao_run_mode_descriptors_and_if02_link(self):
        self.attach('1-4', '1d50', '6197', 'TLZ4A6', 'Dabao')
        self.attach_port('usb-Baochip_Dabao_TLZ4A6-if02', 'ttyACM0')
        device = next(d for d in discover(self.usb, self.by_id) if d['id'] == 'dabao')
        self.assertTrue(device['connected'])
        self.assertTrue(device['serial_link_available'])
        self.assertEqual((device['vid'], device['pid']), ('1d50', '6197'))
        self.assertEqual(device['observed_product'], 'Dabao')
        self.assertEqual(Path(device['persistent_port']).name, 'usb-Baochip_Dabao_TLZ4A6-if02')
        self.assertIn('version unverified', device['device_role_hint'])

    def test_vid_pid_alone_does_not_identify_a_board(self):
        self.attach('1-3', '1a86', '55d4', 'OTHER', 'USB Single Serial')
        devices = {item['id']: item for item in discover(self.usb, self.by_id)}
        self.assertFalse(devices['m5stick']['connected'])

    def test_topology_mismatch_does_not_identify_a_board(self):
        self.attach('1-7', '1a86', '55d4', '5B1E046678', 'USB Single Serial')
        self.attach_port('usb-1a86_USB_Single_Serial_5B1E046678-if00', 'ttyACM4')
        devices = {item['id']: item for item in discover(self.usb, self.by_id)}
        self.assertFalse(devices['m5stick']['connected'])

    def test_missing_persistent_port_keeps_usb_presence_separate(self):
        self.attach('1-4', '1d50', '6196', 'TLZ4A6', 'Baochip-1x')
        devices = {item['id']: item for item in discover(self.usb, self.by_id)}
        self.assertTrue(devices['dabao']['connected'])
        self.assertTrue(devices['dabao']['usb_present'])
        self.assertFalse(devices['dabao']['serial_link_available'])
        self.assertIsNone(devices['dabao']['persistent_port'])

    def test_disconnect_and_reconnect_are_reflected_on_each_scan(self):
        dev = self.attach('1-3', '1a86', '55d4', '5B1E046678', 'USB Single Serial')
        link = self.by_id / 'usb-1a86_USB_Single_Serial_5B1E046678-if00'
        self.attach_port(link.name, 'ttyACM1')
        history = {}
        self.assertTrue(next(d for d in discover(self.usb, self.by_id, history, 't1') if d['id'] == 'm5stick')['connected'])
        link.unlink()
        self.assertTrue(next(d for d in discover(self.usb, self.by_id, history, 't2') if d['id'] == 'm5stick')['connected'])
        for child in dev.iterdir():
            child.unlink()
        dev.rmdir()
        disconnected = next(d for d in discover(self.usb, self.by_id, history, 't3') if d['id'] == 'm5stick')
        self.assertFalse(disconnected['connected'])
        self.assertEqual(disconnected['connection_event'], 'disconnected')
        self.assertEqual(disconnected['last_connection_change_at'], 't3')
        self.assertEqual(disconnected['last_verified_at'], 't2')
        dev.mkdir()
        for key, value in {'idVendor': '1a86', 'idProduct': '55d4', 'serial': '5B1E046678'}.items():
            (dev / key).write_text(value)
        link.symlink_to(self.tty / 'ttyACM1')
        reconnected = next(d for d in discover(self.usb, self.by_id, history, 't4') if d['id'] == 'm5stick')
        self.assertTrue(reconnected['connected'])
        self.assertEqual(reconnected['connection_event'], 'connected')
        self.assertEqual(reconnected['last_connection_change_at'], 't4')


if __name__ == '__main__':
    unittest.main()
