# Manjaro Environment Report

**Captured:** 2026-11-11 (Asia/Kolkata)  
**Host:** Manjaro Linux rolling, x86_64, kernel 6.12.108-1-MANJARO; Ryzen 3 3250U, 4 logical CPUs, 9.6 GiB RAM.  
**Workspace:** 404 GiB free on `/dev/sda2` (Btrfs).

## Verified tools

| Tool | Version/state |
|---|---|
| GCC/G++ | 16.2.1 |
| Python / pip | 3.14.7 / 26.2.1 |
| Make | 4.4.1 |
| Perl | 5.42.2 |
| LZ4 | 1.10.0 |
| Node/npm/pnpm | 26.8.1 / 11.12.1 / 11.3.0 |
| Verilator | 5.052 (`verilator` package 5.052-1, Manjaro extra) |
| Zig | Not installed; intentionally held pending upstream version verification |
| Rust/cargo | Not found |

## Dabao USB evidence (read-only)

Kernel log identified USB VID:PID `1d50:6196`, Baochip-1x, manufacturer Baochip, serial `TLZ4A6`, USB path `1-4`. Kernel attached CDC ACM `ttyACM0` and USB mass-storage interface; block device `/dev/sdb1` has FAT label `BAOCHIP` and is mounted at `/run/media/tanmaymanjaro/BAOCHIP` by the OS. No contents were accessed, copied, modified, or written. `/dev/ttyACM0` was not opened. M5Stick is not connected per user.

`lsusb` failed to initialize libusb in this session; kernel enumeration supplied device identity. `journalctl` reported unavailable system bus for `hostnamectl`; direct OS/kernel data were captured instead.

## Network diagnosis

`getent ahosts github.com pypi.org` returned no addresses; `curl -I --connect-timeout 5 https://github.com/baochip/bio-sim` failed with curl exit 6, “Could not resolve host: github.com”. No proxy variables were configured. Earlier shell attempts to reach GitHub and PyPI also failed DNS resolution. No unverified mirror was used.

## Commands/evidence

- `bash scripts/discover-manjaro.sh` — exit 0; read-only discovery completed.
- `pacman -Si verilator` — official `extra`, version 5.052-1, 7.66 MiB download, 30.90 MiB installed; dependencies Perl, Python, LZ4, zlib; all present before installation.
- User confirmed approved installation completed.
- `verilator --version` — `Verilator 5.052 2026-09-05 rev v5.052`.
- `pacman -Q verilator` — `verilator 5.052-1`.
- `git remote -v` — origin is `git@github.com:Tanmay-say/CrossBar_Dabao_BIOscope.git`; no push performed.
