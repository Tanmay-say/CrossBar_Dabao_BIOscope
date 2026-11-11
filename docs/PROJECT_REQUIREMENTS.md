# BIOScope Product Requirements

## Product
BIOScope is an open-silicon hardware security and programmable-I/O laboratory based on the Baochip-1x Dabao evaluation board, with an M5Stack M5StickC Plus2 operator interface and a Manjaro PC as host.

**Tagline:** Explore, simulate, execute and inspect programmable I/O on open RISC-V silicon.

## Hardware and constraints
- Dabao board + M5StickC Plus2 + Manjaro PC.
- Each board connects independently to the PC by USB data cable.
- No jumper wires, breadboard, external modules, or external sensors.
- No direct board-to-board GPIO/electrical connection.
- No external bus sniffing or logic-analyzer claims without actual wiring.
- Do not modify the Dabao BAOCHIP update volume without a reviewed procedure.
- Do not assume chip-level features are exposed through a usable API.

## Roles
- Dabao: target silicon and BIO/Xous experimentation.
- M5Stick: portable menu/status/controller, only over a verified transport.
- Manjaro: build host, simulator, USB/serial bridge, artifact collector, dashboard.

## Core journeys
1. Select a BIO experiment.
2. Validate config.
3. Compile/simulate using official BIO-sim workflow.
4. Collect logs, waveforms and metadata.
5. Optionally execute on hardware only after target, firmware, pads and loader are verified and user approves.
6. Present honest status in dashboard and M5Stick.

## Functional priorities
### P0
- Manjaro host discovery and environment report.
- Current BIO-sim dependencies/build workflow verified from upstream.
- At least one baseline build and simulation, or a precise blocker.
- Device inventory with evidence-based identity.
- Experiment registry with mode and safety metadata.
- Structured logs, run IDs and artifact index.
- Dashboard for devices, experiments, simulation, logs and artifacts.
- Mock adapters and tests.
- Explicit distinction between compile, simulation and physical execution.

### P1
- M5Stick display/button UI.
- Python host bridge with robust framing/reconnects.
- Waveform viewer if upstream output supports it.
- Dabao/Xous documented example build.

### P2
- Approved physical BIO execution.
- Crypto/TRNG/key-store experiment only if APIs are verified.
- Optional local test-message signing; no real funds and no secret export.

## Non-functional
- Reproducible builds and recorded versions.
- No secrets in code/logs/artifacts.
- Safe failure on timeout, disconnect or malformed response.
- Modular adapters; simulation works without boards.
- Native Manjaro preferred; no Docker/WSL.
- Demo-friendly technical UI.

## Out of scope
- Board-to-board electrical link.
- External logic analysis without wiring.
- Production security certification.
- Real-money blockchain transactions.
- Automated flashing without approval.

## Definition of done
- Host discovery recorded.
- BIO-sim requirements verified.
- Minimal example builds and simulates, or blocker documented.
- Logs/artifacts retained.
- Dashboard displays run evidence and mode.
- M5Stick transport path documented.
- Clean-checkout setup and demo instructions work.
