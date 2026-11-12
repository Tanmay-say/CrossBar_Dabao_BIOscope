# Getting started on Manjaro

This runbook starts the local API and Vite dashboard. It performs device discovery by reading USB sysfs metadata and `/dev/serial/by-id`; it does not open either board's serial port.

## Prerequisites

- Python 3.11 or newer (the verified workspace environment is Python 3.14.7).
- Node.js and npm (verified here as Node 26.8.1 and npm 11.12.1).
- Verilator 5.052 for BIO-sim builds and `gtkwave` for viewing FST files.
- The repository checkout, including the pinned `vendor/bio-sim` submodule.

On a fresh Manjaro install, the native repository packages can be installed with:

```bash
sudo pacman -S --needed python nodejs npm git verilator gtkwave
```

The checked official Manjaro/Arch repositories provide all six packages. This is only a setup command; it was not run as part of this validation. If `vendor/bio-sim` is an uninitialized submodule in a fresh checkout, initialize its pinned revision with:

```bash
git submodule update --init --recursive
```

Check the installed tools:

```bash
python3 --version
node --version
npm --version
verilator --version
gtkwave --version
```

From the project root, validate the existing Python environment and install the locked frontend dependencies if needed:

```bash
cd ~/CrossBar_Dabao_BIOscope
test -x .venv/bin/python || python3 -m venv .venv
./.venv/bin/python -m pip check
cd apps/dashboard
npm ci
cd ../..
```

The API uses Python's standard library for its HTTP server. `pyserial` is needed only by the separately gated Dabao adapter; no serial action is part of starting the app.

The current simulator build was verified with project-local Zig 0.15.2. To reproduce BIO C builds in a new environment, use the upstream-verified version in the project virtual environment:

```bash
./.venv/bin/python -m pip install ziglang==0.15.2
```

This optional compiler install is not needed merely to start the API and dashboard or view already-generated local artifacts.

## Start the application

Open two terminals at the repository root.

**Terminal 1 — backend API:**

```bash
cd ~/CrossBar_Dabao_BIOscope
./.venv/bin/python apps/host/server.py --host 127.0.0.1 --port 8765
```

The API listens on `http://127.0.0.1:8765`.

**Terminal 2 — dashboard:**

```bash
cd ~/CrossBar_Dabao_BIOscope/apps/dashboard
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`. Vite forwards `/api` requests to the API on port 8765. The production build is served by the API at `http://127.0.0.1:8765` after `npm run build`.

## Verify the live API and hardware inventory

In a third terminal:

```bash
curl -fsS http://127.0.0.1:8765/api/health
curl -fsS http://127.0.0.1:8765/api/hardware/capabilities
curl -fsS http://127.0.0.1:8765/api/devices
curl -fsS http://127.0.0.1:8765/api/experiments
```

Device inventory is descriptive only. USB identity matching uses the profile, product descriptor, VID/PID, serial, topology and persistent link together. The M5Stick USB descriptors identify its USB-UART bridge; the association with the M5StickC Plus2 is operator-correlated. No serial communication with Bruce is implemented or enabled.

## View the recorded Dabao verification

The physical run is historical evidence, not a new live execution. In the dashboard, open **Run History** and select run `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`. It records `HARDWARE_VERIFIED`, expected FIFO0 `0xB105C0DE`, and actual FIFO0 `0xB105C0DE`.

The local raw evidence is in the ignored `artifacts/runs/<run-id>/` directory. For a shareable, sanitized copy, see [`hardware-evidence/public/`](hardware-evidence/public/). The public copy redacts device serials and host-specific paths, and includes its own checksum index. The source run files were not changed.

The app exposes run manifests, stdout, stderr, hardware result and the manifest amendment through the API. For direct checks, use:

```bash
curl -fsS http://127.0.0.1:8765/api/runs/d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62
curl -fsS http://127.0.0.1:8765/api/runs/d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62/artifacts/manifest.json
curl -fsS http://127.0.0.1:8765/api/runs/d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62/artifacts/hardware-result.json
curl -fsS http://127.0.0.1:8765/api/runs/d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62/artifacts/stdout.log
```

Artifact URLs for the physical run are dashboard/API paths; public evidence files are separately sanitized repository copies.

## Open a simulation waveform

Choose a genuine blink run in **Run History** or **Waveform Viewer**. One existing verified simulation trace is:

```bash
gtkwave artifacts/runs/ad1120e1-3214-4e7d-b334-20f84e28c15b/trace.fst
```

This FST is simulation evidence, not physical GPIO evidence. In GTKWave, inspect the BIO GPIO output bus and bit 21; compare transitions with the same simulation run's stdout. The API also serves the waveform artifact when its run ID and artifact name are selected in the UI.

## Stop cleanly

Press `Ctrl+C` in Terminal 2 to stop Vite, then in Terminal 1 to stop the API. No background process or serial session should remain.

## Troubleshooting

- **Port 8765 or 5173 is occupied:** inspect the process holding it (`ss -ltnp`) and stop only the process you started. Do not kill unrelated services.
- **API health fails:** start Terminal 1 first and check its console for a bind or Python error. The frontend proxy target is `http://127.0.0.1:8765`.
- **Dashboard dependencies are missing:** run `npm ci` from `apps/dashboard`; it uses the committed lockfile.
- **Python dependencies are inconsistent:** run `./.venv/bin/python -m pip check`. Do not install system packages for the API's standard-library server.
- **A board is absent:** inspect USB inventory and `/dev/serial/by-id` links read-only. Do not open a port or change udev permissions as a discovery test. Connection status can differ between this host and another machine.
- **No local hardware run appears:** the ignored raw run folder is machine-local. Use the sanitized public evidence folder for review; do not copy it into the live run directory or label it a new hardware execution.
- **GTKWave cannot open the FST:** confirm the referenced simulation run contains a non-empty `trace.fst`, `gtkwave --version` works, and the graphical session is available.

For the limitations and current verification levels, see [`DEMO_READINESS.md`](DEMO_READINESS.md) and [`SAFETY_AND_HARDWARE.md`](SAFETY_AND_HARDWARE.md).
