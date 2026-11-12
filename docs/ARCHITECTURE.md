# BIOScope Architecture

```text
Dabao board --USB-->                    +---------------------+
                                        |                     |
M5Stick Plus2 --USB--> Manjaro PC ------| Python host bridge  |
                                        | discovery/adapters  |
                                        | run orchestration   |
                                        +-----+-----------+---+
                                              |           |
                                         BIO-sim       Local API
                                         C source      HTTP/events
                                         Verilator         |
                                         toolchain         v
                                              |       React + TS
                                         logs/FST      dashboard
```

This is logical architecture, not proof that a device protocol or hardware execution path exists. Both boards are independently USB-connected; no direct board link is assumed. The current Bruce device is not connected to the BIOScope bridge because Linux CDC ACM open behavior can assert DTR/RTS.

## Current data flow

```mermaid
flowchart LR
  UI[React dashboard] -->|HTTP JSON| API[Python host API]
  API --> REG[Experiment catalog and validator]
  REG --> SIM[BIO-sim allow-listed adapter]
  SIM --> RTL[Verilator simulation]
  RTL --> OUT[Logs, manifest, FST]
  OUT --> API
  API --> UI
  STICK[M5Stick Plus2 running Bruce] -. identity discovery only; no serial open .-> API
  FW[Future BIOScope firmware] -. versioned JSONL protocol, mock tested only .-> BRIDGE[Fail-closed M5Stick bridge]
  BRIDGE -. catalog allow-list only .-> ENG[Same experiment engine]
  DAB[Dabao USB CDC] -. descriptor discovery only .-> API
  DAB -. hardware console disabled .-> GUARD[No hardware commands or flashes]
```

M5Stick transport framing is prepared for a separately installed BIOScope firmware, but the connected device is operator-associated with Bruce firmware. Bruce has a different, broad serial command interface; BIOScope does not open the port or run its bridge against Bruce. The physical opener raises `PhysicalSerialDisabled` after identity preflight; mock transports exercise the bounded protocol and allow-listed catalog handler. Dabao console remains unopened because boot1's documented serial interface can accept updates and commands, while the active stage is unverified. USB identity discovery uses exact VID/PID + serial + physical topology plus the persistent by-id link and does not open either port.

## Components
- BIO-sim adapter: wraps official upstream build/run scripts, captures command, exit code, logs, versions, revision and artifacts.
- Dabao adapter: evidence-based discovery; documented console/loader only; writes gated by approval.
- M5Stick adapter: verified USB identity, versioned bounded mock protocol, catalog-only run requests; physical serial is fail-closed while Bruce is installed.
- Python host: device discovery, experiment registry, run orchestration, API, logs and artifact index.
- Dashboard: React + TypeScript + Vite; Overview, Devices, Experiments, Runs, Waveforms/Artifacts, Logs, Diagnostics.
- M5Stick UI: status, host link, experiment menu, progress, result, errors.
- Device discovery: read-only sysfs/interface-driver plus `/dev/serial/by-id` inspection; per-profile matching requires VID/PID, unique USB serial and recorded topology. Dashboard status refreshes every 2 seconds.

The current host API is `apps/host/server.py`; the typed React dashboard is `apps/dashboard/src/`. The simulator adapter supports only fixed catalog entries/configs (`smoke.jsonc`, `blink.jsonc`) and never accepts arbitrary commands. Runs retain a JSON manifest, separate stdout/stderr and copied artifacts under `artifacts/runs/<run_id>/`. Current M5Stick frames are a prepared protocol sketch; there is not yet an active host serial bridge.

## Suggested repository layout
```text
bioscope/
├── .agents/skills/bioscope-engineer/SKILL.md
├── apps/dashboard/
├── apps/host/
├── firmware/m5stick-plus2/
├── adapters/{bio_sim,dabao,m5stick}/
├── experiments/{registry,bio}/
├── docs/ plans/ progress/ reports/ scripts/
└── artifacts/                 # ignored by Git
```
Adapt to existing repo; do not overwrite it blindly.

## Suggested API
- GET /api/health
- GET /api/devices
- GET /api/experiments
- POST /api/runs
- GET /api/runs/{run_id}
- GET /api/runs/{run_id}/logs
- GET /api/runs/{run_id}/artifacts
- Optional WebSocket /api/events

Each run records ID, experiment, mode, config hash, source revision, tool versions, timestamps, exit code and evidence.

## Experiment contract
Each experiment declares ID, title, objective, allowed modes (MOCK/SIMULATION/COMPILE_ONLY/HARDWARE), dependencies, input schema, validated command/adapter, outputs, safety class and evidence requirements. Never accept arbitrary shell commands from UI.

## Protocol
Versioned framing with message type, request ID, bounded payload, timeout, explicit errors. Test malformed frames, truncation, duplicate IDs and disconnects. No credentials or private keys in messages.

## Run states
QUEUED -> VALIDATING -> BUILDING -> SIMULATING -> COMPLETED/FAILED.
Hardware path separately: QUEUED -> VALIDATING -> AWAITING_APPROVAL -> RUNNING -> HARDWARE_RESULT_CAPTURED.
A simulator completion is never hardware verification.
