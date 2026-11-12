# Manjaro Environment Report

**Initial capture:** 2026-11-11 (Asia/Kolkata); current revalidation follows.
**Host:** Manjaro Linux rolling, x86_64, kernel 6.12.108-1-MANJARO; Ryzen 3 3250U, 4 logical CPUs, 9.6 GiB RAM.  
**Workspace:** 404 GiB free on `/dev/sda2` (Btrfs).

## Verified tools at initial capture

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

## Historical Dabao USB evidence (read-only)

Kernel log identified USB VID:PID `1d50:6196`, Baochip-1x, manufacturer Baochip, serial `[Dabao serial redacted]`, USB path `1-4`. Kernel attached CDC ACM `ttyACM0` and USB mass-storage interface; block device `/dev/sdb1` has FAT label `BAOCHIP` and is mounted at `mounted BAOCHIP volume` by the OS. No contents were accessed, copied, modified, or written. `/dev/ttyACM0` was not opened. M5Stick is not connected per user.

`lsusb` failed to initialize libusb in this session; kernel enumeration supplied device identity. `journalctl` reported unavailable system bus for `hostnamectl`; direct OS/kernel data were captured instead.

## Historical network diagnosis (2026-11-11)

`getent ahosts github.com pypi.org` returned no addresses; `curl -I --connect-timeout 5 https://github.com/baochip/bio-sim` failed with curl exit 6, “Could not resolve host: github.com”. No proxy variables were configured. Earlier shell attempts to reach GitHub and PyPI also failed DNS resolution. No unverified mirror was used.

## Commands/evidence

- `bash scripts/discover-manjaro.sh` — exit 0; read-only discovery completed.
- `pacman -Si verilator` — official `extra`, version 5.052-1, 7.66 MiB download, 30.90 MiB installed; dependencies Perl, Python, LZ4, zlib; all present before installation.
- User confirmed approved installation completed.
- `verilator --version` — `Verilator 5.052 2026-09-05 rev v5.052`.
- `pacman -Q verilator` — `verilator 5.052-1`.
- `git remote -v` — origin is `git@github.com:Tanmay-say/CrossBar_Dabao_BIOscope.git`; no push performed.

## Current revalidation (2026-11-12)

- User supplied `getent hosts github.com` and `curl -I https://github.com` success (`HTTP/2 200`). Official BIO-loader and sparse Xous source fetches subsequently succeeded, confirming GitHub access restored for these sources.
- Current read-only sysfs scan: Dabao `1d50:6197`, product `Dabao`, serial `[Dabao serial redacted]`, topology `1-4`; interfaces 00/01 use `usbhid`, 02/03 use `cdc_acm`. M5Stick operator-correlated USB bridge: `1a86:55d4`, product `USB Single Serial`, serial `[M5Stick bridge serial redacted]`, topology `1-3`; interfaces use `cdc_acm`. Descriptors identify the USB bridge and operator association, not the M5Stack model by themselves.
- This execution sandbox can read USB sysfs descriptors but cannot see `/dev/serial/by-id` or `/dev/ttyACM*`; API reports serial links unavailable in this context. This differs from earlier host-level udev observations; no port was opened to resolve it.
- Current project-local Zig: `0.15.2` (`.venv`, Python `ziglang` package). Verilator `5.052`; GTKWave `3.3.128` was installed by the user and previously loaded BIO-sim FSTs. `cargo`, `rustc`, and `rustup` are absent; no Xous Rust toolchain installation was attempted.
- Current upstream Xous source snapshot: `99bbfcc15320561f09a97e9ebb5e05a673ca3379`; official bio-loader source: `a827a3c944c44c1b507e4eab55c76fc67871a8ca`. Installed Dabao Xous/app version remains unverified.
- Current user is not in `uucp`; prior host snapshot reported `/dev/ttyACM0` mode `root:uucp` 0660. No group, rule, or permission changes were made.
- BAOCHIP volume contents were not accessed; no serial, firmware or update operation was attempted during this work.
