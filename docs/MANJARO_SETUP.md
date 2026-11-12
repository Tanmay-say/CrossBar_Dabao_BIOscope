# Manjaro Setup — Discovery First

No installation should happen during initial discovery. Manjaro is the primary native host; no Docker or WSL is required.

## Discovery
Run `bash scripts/discover-manjaro.sh`. Also inspect:
```bash
cat /etc/os-release
uname -a
lscpu
free -h
df -hT
rustc --version
cargo --version
python --version
gcc --version
clang --version
zig version
verilator --version
make --version
perl --version
lz4 --version
node --version
npm --version
git --version
```
Missing commands are normal; do not install automatically.

## BIO-sim verification
Read current upstream README, scripts, examples and CI:
https://github.com/baochip/bio-sim

Verify Linux support and exact Zig, Verilator, C compiler, Python, Make, Perl, LZ4, waveform tool requirements, exact baseline command and outputs. Record upstream commit. Do not rely on stale dependency lists.

## Package policy
Check official Manjaro/Arch repositories first (`pacman -Ss`, `pacman -Si`). Before installing, report package names, source (official/AUR/upstream), versions, download and installed size, and system changes. Ask approval. Review AUR PKGBUILDs; never run opaque scripts.

## Xous
Read current Baochip Xous README and bootchain docs. Verify target, Rust toolchain, build commands and recovery path. Build-only first; no flashing.

## M5Stick
Use exact Plus2 documentation: https://docs.m5stack.com/en/core/StickC-Plus2. Verify model revision, framework, display/buttons, USB transport and flashing process. Build minimal app first; ask before flashing.

## Disk discipline
Inspect free space before downloads/builds. Keep build artifacts under ignored project-local folders. Avoid duplicate clones/toolchains. Do not clear global caches without reporting size and asking.

## Verified BIOScope build paths

For this workspace, verified simulator source is the `vendor/bio-sim` submodule at commit `7e9c9615e1c900c7ddae1c4645a87078b217abc3`. Run its documented `make build`, then `./simulate configs/smoke.jsonc` or `./simulate configs/blink.jsonc`. Blink firmware uses the upstream-tested Zig 0.15.2 (project `.venv`); run `python -m ziglang build -Dmodule=blink -Demit-listing=false` from the upstream `sw/` directory when rebuilding it.

The React dashboard requires Node/npm: `cd apps/dashboard && npm ci && npm run build`. Start API using `python3 apps/host/server.py`, then visit `http://127.0.0.1:8765`.

To build Plus2 firmware without flashing: create/reuse `.venv`, install `platformio==6.2.0` there, then run `scripts/build-m5stick.sh`. This uses a project-local PlatformIO cache and pinned M5Unified/ArduinoJson dependencies. Never use an upload target without explicit approval.

The USB inventory API reads `/sys/bus/usb/devices` and `/dev/serial/by-id`; it does not open serial ports. The dashboard refreshes device state every two seconds. Do **not** run `apps/host/m5stick_bridge.py` against the installed Bruce firmware: it expects the BIOScope JSON protocol, which Bruce does not document. Bruce is preserved. Both serial links remain unopened; see `docs/DEVICE_DISCOVERY.md` before any physical communication. Serial access, firmware upload, bootloader action and update-volume access require separate safety review and approval.
