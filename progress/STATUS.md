# BIOScope Status

**Date:** 2026-11-11  
**State:** Official BIO-sim smoke, register-inspection and blink simulations pass; React dashboard runs against the host API with genuine FST artifacts.

## Latest waveform and protocol milestone
- GTKWave Analyzer 3.3.128 verified; smoke, register-inspection and blink FSTs opened successfully (FSTLOAD reported 13,485 facilities, 5,001 signals and 8,484 aliases per file).
- Blink GPIO 21 FST edges verified against simulator logs; dashboard now has an Open in GTKWave action with missing-display/viewer handling.
- Host M5Stick JSON framing/request handler prepared and unit tested; no physical serial link opened.
- Latest tests: 20 backend/API/simulator/protocol tests pass; Python compile and React/TypeScript build pass.

## Functional now
- Start host with `python3 apps/host/server.py`; dashboard at `http://127.0.0.1:8765`.
- API health, experiment catalog, read-only USB sysfs inventory, run creation/history/detail.
- Mock orchestration with strict input/mode checks, logs, exit code, structured manifest and clearly marked placeholder artifact.
- Official BIOScope simulation adapter invokes only upstream `configs/smoke.jsonc`; captures stdout/stderr, exit status, run metadata and FST.
- Official upstream blink built using local Zig 0.15.2 (`-Demit-listing=false`, because optional RISC-V objdump is absent), then ran at 10,000 cycles with repeated GPIO 21 edges.
- Manjaro GTKWave package compatibility confirmed from official Arch package file list (FST reader/converter/examples). Package install is still awaiting sudo authentication; viewer has not yet been opened.
- React + TypeScript + Vite dashboard has production build and serves via host API. Includes selectable MOCK/SIMULATION, run history, validation/signal transitions, metadata and artifact download.
- `python3 -m unittest discover -s apps/host -v`: 10 passing tests; `py_compile` and `npm run build` pass.

## Verified boundaries
- Verilator 5.052 installed. Kernel previously identified Dabao as Baochip-1x (`1d50:6196`, serial `TLZ4A6`) and `/dev/ttyACM0`; adapter only reads sysfs descriptors and does not open serial.
- `BAOCHIP` stays untouched; no physical execution or firmware changes.
- M5Stick remains disconnected; exact Plus2 firmware framework is unverified and not built.
- BIO-sim source commit: `7e9c9615e1c900c7ddae1c4645a87078b217abc3`. Smoke and register inspection pass cfginfo `0x10000408`; blink shows GPIO 21 transitions. Genuine FSTs: 46,301-byte smoke, 107,364-byte blink.
- Zig 0.15.2 installed project-locally only. GTKWave install pending user sudo; package command: `sudo pacman -S --needed gtkwave`.

## Blocker and next step
- Execution sandbox still cannot resolve GitHub directly; elevated network access succeeded for the official clone and upstream JSON header. No host network settings changed.
- Frontend currently uses zero-dependency HTML/JS because network is unavailable; React/TypeScript/Vite is not installed or claimed.

See `docs/ENVIRONMENT_REPORT.md`, `docs/TOOLCHAIN_PLAN.md`, `docs/HARDWARE_INTEGRATION.md` and `docs/DEMO.md`. No physical hardware execution has occurred.
