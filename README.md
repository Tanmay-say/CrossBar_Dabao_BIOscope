# BIOScope

BIOScope is an open-silicon programmable-I/O laboratory for Baochip-1x Dabao, operated from a Manjaro Linux host. It combines three verified BIO-sim experiments, genuine FST evidence, waveform inspection, a run API and a React engineering dashboard. USB identity discovery is read-only. Physical board command execution is deliberately disabled until a safe protocol is verified.

## Current project state

This repository is the fresh BIOScope project root created from the Manjaro Starter Kit. Read `docs/PROJECT_REQUIREMENTS.md`, `docs/ARCHITECTURE.md`, `docs/SAFETY_AND_HARDWARE.md`, `docs/MANJARO_SETUP.md`, and `progress/STATUS.md` before hardware work. The read-only host discovery helper is `scripts/discover-manjaro.sh`.

## Safety and operating constraints

- Dabao and M5Stick connect independently to the Manjaro PC by USB. Do not connect their pins together or assume external wiring, sensors, or logic analysis.
- Never alter the Dabao `BAOCHIP` update volume without a separately reviewed procedure and explicit approval.
- Do not guess serial devices, baud rates, pin maps, firmware names, or loader commands.
- Report compile, simulation, and physical execution as distinct evidence levels.
- No Docker or WSL requirement. Prefer native packages and verified upstream sources.
- Do not commit secrets or generated binaries.

## Project layout

- `docs/` — requirements, architecture, safety, setup, and verified toolchain/environment reports.
- `progress/` — current status and chronological activity log.
- `plans/` — implementation backlog.
- `prompts/` — project handoff prompt.
- `scripts/` — read-only discovery and later orchestration helpers.

## Run the demo

```sh
python3 apps/host/server.py
```

Open `http://127.0.0.1:8765`. The Hardware Devices page shows independently matched USB profiles, independent link status, topology, interface driver and verification/change timestamps without opening serial. The M5Stick association is operator-correlated; its USB descriptor identifies the QinHeng USB bridge only. To run checks and build the dashboard:

```sh
python3 -m unittest discover -s apps/host -v
cd apps/dashboard && npm run build
```

Use SIMULATION for the upstream smoke, register-inspection and blink targets. MOCK is clearly marked and only exercises the host pipeline. The demo walkthrough is in `docs/DEMO.md`; upstream source commit and actual run evidence are in `docs/TOOLCHAIN_PLAN.md` and `artifacts/`. Open a verified FST from a run in GTKWave using the dashboard action or `gtkwave <path-to-trace.fst>`.

Build the Plus2 firmware without uploading it with `scripts/build-m5stick.sh` after installing PlatformIO in the project `.venv`. Bruce remains installed on the connected M5Stick. Linux CDC ACM opening can assert DTR/RTS, so BIOScope did not send Bruce's documented `info` request; the bridge fails closed before opening a port. See `docs/DEVICE_DISCOVERY.md` and `docs/M5STICK_FIRMWARE_CHANGE_PROPOSAL.md`. The Dabao console and update volume are not accessed.

## Current limitations

- BIO-sim is an RTL simulation; it does not prove physical Dabao GPIO behavior.
- Plus2 firmware compiles but has not been flashed or exercised on a physical M5Stick.
- M5Stick association is correlated by the user-reported connection, USB arrival, bridge serial and topology; the descriptors themselves identify only the QinHeng USB-UART bridge.
- Bruce remains intact, but no physical Bruce diagnostics or BIOScope protocol exchange has been performed; opening the serial device is not proven reset-free.
- Dabao USB serial protocol/stage is not identified safely, and no hardware command has been sent.

## Official references

- [Baochip BIO-sim](https://github.com/baochip/bio-sim)
- [Baochip-1x Dabao introduction](https://baochip.com/dabao-intro/)
- [Dabao hardware repository](https://github.com/baochip/dabao)
- [Baochip Xous README](https://github.com/betrusted-io/xous-core/blob/dev/README-baochip.md)
- [Xous core](https://github.com/betrusted-io/xous-core)
- [M5Stack M5StickC Plus2 documentation](https://docs.m5stack.com/en/core/StickC-Plus2)
- [CrossBar Dabao Hackathon](https://crossbar-inc.com/pages/dabao-hackathon)

The M5Stick and hardware integration status is documented in `docs/HARDWARE_INTEGRATION.md`, `docs/DEVICE_DISCOVERY.md` and `docs/M5STICK_FIRMWARE_CHANGE_PROPOSAL.md`.

Upstream build instructions and versions must be checked from current source before use; see `docs/TOOLCHAIN_PLAN.md`.
