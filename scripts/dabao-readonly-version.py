#!/usr/bin/env python3
"""One-shot, exact-profile Dabao Xous version query; never sends BIO commands.

This script intentionally opens the USB CDC port. Linux/USB control-line
behavior may reset a board even with DTR/RTS requested low. Do not run until
the operator explicitly approves that physical action.
"""
from pathlib import Path
import sys
import time
import argparse

PROFILE = {
    "topology": "1-4", "vid": "1d50", "pid": "6197",
    "serial": "TLZ4A6", "product": "Dabao",
    "by_id": "usb-Baochip_Dabao_TLZ4A6-if02",
}
SYS_USB = Path("/sys/bus/usb/devices")
BY_ID = Path("/dev/serial/by-id")


def _read(path):
    try:
        return path.read_text().strip()
    except OSError:
        return None


def resolve_verified_port(sys_usb=SYS_USB, by_id=BY_ID, tty_sys=Path("/sys/class/tty")):
    device = sys_usb / PROFILE["topology"]
    observed = {key: _read(device / field) for key, field in
                (("vid", "idVendor"), ("pid", "idProduct"), ("serial", "serial"), ("product", "product"))}
    if not device.is_dir() or any(observed[k] != PROFILE[k] for k in PROFILE if k != "topology" and k != "by_id"):
        raise RuntimeError("connected USB descriptors do not match the exact Dabao profile")
    link = by_id / PROFILE["by_id"]
    try:
        tty = link.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RuntimeError("exact persistent Dabao serial link is unavailable") from exc
    if tty.parent != Path("/dev") or not tty.name.startswith("ttyACM"):
        raise RuntimeError("persistent link does not resolve to a USB CDC ACM node")

    interface = (tty_sys / tty.name / "device").resolve(strict=True)
    usb_parent = next((parent for parent in interface.parents if (parent / "idVendor").is_file()), None)
    if usb_parent is None or usb_parent.resolve() != device.resolve():
        raise RuntimeError("tty sysfs ancestry does not match the exact Dabao USB device")
    return link


def query_version(serial_module=None, port_resolver=resolve_verified_port, monotonic=time.monotonic):
    if serial_module is None:
        import serial as serial_module
    port = port_resolver()
    connection = serial_module.Serial(port=None, baudrate=1_000_000,
                                      bytesize=serial_module.EIGHTBITS,
                                      parity=serial_module.PARITY_NONE,
                                      stopbits=serial_module.STOPBITS_ONE,
                                      timeout=0.2, write_timeout=1,
                                      exclusive=True)
    connection.dtr = False
    connection.rts = False
    connection.port = str(port)
    connection.open()
    try:
        # Exactly one official, read-only Xous version command; never retry.
        connection.write(b"ver xous\r\n")
        deadline = monotonic() + 5.0
        response = []
        while monotonic() < deadline:
            raw = connection.readline()
            if raw:
                line = raw.decode("utf-8", errors="replace").strip()
                response.append(line)
                if "Xous version:" in line:
                    return {"command": "ver xous", "response": line, "all_lines": response,
                            "port": str(port), "baud": 1_000_000, "dtr": False, "rts": False}
        raise TimeoutError("no Xous version response within 5 seconds; no second command was sent")
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accept-possible-reset", action="store_true",
                        help="confirm that opening USB CDC can reset the target")
    args = parser.parse_args(argv)
    if not args.accept_possible_reset:
        parser.error("no serial port was opened; review the hardware safety note and pass --accept-possible-reset only after explicit approval")
    try:
        result = query_version()
    except Exception as exc:
        print(f"Dabao read-only version query failed: {exc}", file=sys.stderr)
        return 1
    print(f"Xous version response: {result['response']}")
    print(f"Persistent path: {result['port']}")
    print("Port closed; no BIO/upload/update command sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
