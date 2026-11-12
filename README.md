# BIOScope

BIOScope is an open-silicon programmable-I/O laboratory for Baochip-1x Dabao, operated from a Manjaro Linux host. It combines three upstream BIO-sim experiments, genuine FST evidence, waveform inspection, a recorded physical BIO FIFO0 result, run API and React engineering dashboard. On 2026-11-12 the approved pin-free BIO FIFO0 probe ran on Dabao under Xous `v0.10.1-43-g8964027ff`; the console returned `b105c0de`, matching expected `0xB105C0DE`. The result is recorded as `HARDWARE_VERIFIED`, separately from simulation runs.

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

Follow [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) for separate backend and Vite terminals, live API checks, recorded-run viewing, and GTKWave commands. The API is `http://127.0.0.1:8765`; Vite is `http://127.0.0.1:5173`.

For the shot-by-shot narration, see [`docs/DEMO_VIDEO_GUIDE.md`](docs/DEMO_VIDEO_GUIDE.md). Current evidence levels and limitations are in [`docs/DEMO_READINESS.md`](docs/DEMO_READINESS.md).

Use SIMULATION for upstream smoke, register-inspection, blink, and the FIFO probe model; these results remain `SIMULATED`. The one physical FIFO probe is a separate `HARDWARE_VERIFIED` record. MOCK is clearly marked and only exercises the host pipeline. The physical run ID is `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`; its captured console output, hardware result and immutable manifest are under `artifacts/runs/<run-id>/` on the originating machine. The checksum-bound metadata amendment is `docs/hardware-evidence/<run-id>-amendment.json`; public sanitized run copies and their recomputed checksums are in [`docs/hardware-evidence/public/`](docs/hardware-evidence/public/). The demo walkthrough is in `docs/DEMO.md`. Open a verified simulation FST using the dashboard or `gtkwave <path-to-trace.fst>`.

Build the Plus2 firmware without uploading it with `scripts/build-m5stick.sh` after installing PlatformIO in the project `.venv`. Bruce remains installed on the connected M5Stick; no M5Stick communication was part of the Dabao run. The approved operation used only Dabao's documented Xous BIO console. The mounted BAOCHIP update volume was not accessed.

## Current limitations

- BIO-sim is an RTL simulation; it does not prove physical Dabao GPIO behavior.
- Plus2 firmware compiles but has not been flashed or exercised on a physical M5Stick.
- M5Stick association is correlated by the user-reported connection, USB arrival, bridge serial and topology; the descriptors themselves identify only the QinHeng USB-UART bridge.
- Bruce remains intact, but no physical Bruce diagnostics or BIOScope protocol exchange has been performed; opening the serial device is not proven reset-free.
- The physical probe verifies one FIFO0 transfer, not GPIO pad behavior, electrical output or board-level pin mapping. No physical GPIO experiment is claimed.
- The approved probe replaced the previous stored BIO image. The documented Xous console has no readback/recovery route for that image. Later hardware runs remain gated and are not exposed as arbitrary dashboard commands.

## Official references

- [Baochip BIO-sim](https://github.com/baochip/bio-sim)
- [Baochip-1x Dabao introduction](https://baochip.com/dabao-intro/)
- [Dabao hardware repository](https://github.com/baochip/dabao)
- [Baochip Xous README](https://github.com/betrusted-io/xous-core/blob/dev/README-baochip.md)
- [Pinned Xous BIO console implementation](https://github.com/betrusted-io/xous-core/blob/8964027fff25f8b85d3d3c63933d365ac7614523/apps-dabao/dabao-console/src/cmds/bio.rs)
- [Xous core](https://github.com/betrusted-io/xous-core)
- [M5Stack M5StickC Plus2 documentation](https://docs.m5stack.com/en/core/StickC-Plus2)
- [CrossBar Dabao Hackathon](https://crossbar-inc.com/pages/dabao-hackathon)

The current Dabao USB identity uses VID/PID, product descriptor, serial, topology and exact interface-02 by-id matching; public docs redact the unique serial and device node. Its Xous version was reported by the operator and the documented BIO command path returned the verified FIFO0 sentinel. The one approved session closed the port afterward and left the update volume untouched. The M5Stick remains associated with Bruce and has not been communicated with. Details: `docs/HARDWARE_INTEGRATION.md`, `docs/DEVICE_DISCOVERY.md`, and `docs/M5STICK_FIRMWARE_CHANGE_PROPOSAL.md`.

Upstream build instructions and versions must be checked from current source before use; see `docs/TOOLCHAIN_PLAN.md`.
