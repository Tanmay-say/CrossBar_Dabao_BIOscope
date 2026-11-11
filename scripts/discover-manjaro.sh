#!/usr/bin/env bash
# Read-only BIOScope Manjaro discovery. Does not open serial ports or mount/write disks.
set +e
section() { printf '\n\n===== %s =====\n' "$1"; }
section "Timestamp and host"
date -Is
hostnamectl 2>&1
cat /etc/os-release 2>&1
uname -a
section "CPU, memory, storage"
lscpu 2>&1
free -h 2>&1
df -hT 2>&1
section "Development tools"
for c in git rustc cargo python python3 pip pip3 gcc g++ clang zig verilator make perl lz4 node npm pnpm yarn; do
  if command -v "$c" >/dev/null 2>&1; then
    printf '\n--- %s ---\n' "$c"
    case "$c" in
      perl) "$c" -v 2>&1 | head -n 3 ;;
      *) "$c" --version 2>&1 | head -n 4 ;;
    esac
  else
    printf '\n--- %s: NOT FOUND ---\n' "$c"
  fi
done
section "USB inventory (read-only)"
if command -v lsusb >/dev/null 2>&1; then lsusb; else echo "lsusb not found"; fi
section "Serial device links"
if [ -d /dev/serial/by-id ]; then ls -l /dev/serial/by-id; else echo "/dev/serial/by-id not present"; fi
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
section "User and serial-related groups"
id
getent group uucp
getent group dialout
getent group lock
section "Utilities"
for c in udevadm journalctl pacman; do
  command -v "$c" >/dev/null 2>&1 && echo "$c: $(command -v "$c")" || echo "$c: NOT FOUND"
done
section "Recent USB kernel messages"
if command -v journalctl >/dev/null 2>&1; then
  journalctl -k -n 80 --no-pager 2>&1 | grep -Ei 'usb|tty|cdc_acm|ch34|wch|serial' | tail -n 50
fi
section "Safety"
echo "No serial ports opened; no filesystem mounted; no package installed; no permission or device changes made."
