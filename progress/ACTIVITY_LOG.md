# Activity Log

## 2026-11-11 — Manjaro starter kit prepared
- Consolidated Dabao + M5Stick requirements and constraints.
- Defined Manjaro native workflow, without Docker/WSL.
- Added Codex skill, read-only discovery script, backlog, and safety gates.
- No package installation, Git operation, serial-port opening, or board write performed by this kit.

## Historical Windows setup (user-provided audit)
- Portable MSYS2 UCRT64 installed under `D:\CrossBar_Dabao_Hackathon\tools\msys64`.
- Make, Perl, UCRT64 GCC, Verilator and dependencies installed there.
- POSIX package transaction interrupted; no completed POSIX installation confirmed.
- No WSL installation confirmed.
- Cleanup was proposed but not executed in the supplied audit.

## 2026-11-11 — BIOScope Manjaro implementation kickoff
- Repaired README: removed a NUL-interleaved suffix that caused Git to treat the file as binary; preserved and integrated starter-kit requirements and official references.
- Ran `bash scripts/discover-manjaro.sh` (exit 0); documented host, tool versions, disk space, Dabao kernel/USB identity and interfaces.
- Confirmed `BAOCHIP` mounted at `/run/media/tanmaymanjaro/BAOCHIP`; left volume contents untouched. Did not open `/dev/ttyACM0`.
- Verified official BIO-sim README describes `make build`, `./simulate configs/smoke.jsonc`, expected `0x10000408`, and FST trace. Retrieved Makefile describes nlohmann/json v3.11.3 fetch.
- Verified and installed only approved official Manjaro `verilator` 5.052-1 (7.66 MiB archive; 30.90 MiB installed; dependencies already present). `verilator --version` reports 5.052.
- GitHub/PyPI DNS unavailable: `curl` to GitHub failed with exit 6; no proxy configured. Official clone failed; no upstream revision or real simulator result claimed. Zig/GTKWave remain uninstalled pending verification.

## 2026-11-11 — Offline vertical slice expanded
- Added local API routes for health, USB sysfs device inventory, experiment catalog, run creation/history/detail.
- Added four-entry evidence-labelled experiment catalog; real BIO-sim and blink remain unavailable pending official source/toolchain verification.
- Reworked mock run execution with strict config/mode validation, timeout/error handling, separate log files, exit codes, persistent manifests and explicit placeholder artifact metadata.
- Replaced placeholder page with responsive dark engineering console backed by live API state, device status, experiment selection, execution, logs, artifacts and run history.
- Added M5Stick Plus2 integration notes and a concise demo runbook; no firmware claimed built.
- Ran `python3 -m unittest discover -s apps/host -v`: 8 tests passed, including API integration, run success/failure, missing simulator/artifact, timeout, malformed config and wrong mode. `py_compile` passed.
- Network/hardware restrictions unchanged: no external source acquisition; no serial opened; BAOCHIP volume untouched.

## 2026-11-11 — Official BIO-sim baseline and dashboard integration
- Acquired official `https://github.com/baochip/bio-sim` at commit `7e9c9615e1c900c7ddae1c4645a87078b217abc3` using elevated network access; the ordinary execution sandbox still cannot resolve GitHub.
- Inspected README, Makefile, smoke config, firmware Zig build script/README, CI workflow, examples and `biowave.py`. Upstream BIO C build states tested Zig 0.15.2 and documents `python3 -m ziglang`; Zig is not needed for the smoke simulator.
- Upstream Makefile fetched official nlohmann/json v3.11.3 header; checksum is documented in `docs/TOOLCHAIN_PLAN.md`.
- `make build` with installed Verilator 5.052 completed, exit 0 (upstream RTL warnings only).
- `./simulate configs/smoke.jsonc` completed, exit 0; cfginfo value `0x10000408` PASS; simulation time 902496 ps, 0 firmware cycles.
- Genuine 46,301-byte `trace.fst` generated; SHA-256 documented. The trace was copied via the new allow-listed BIOScope simulation adapter into `artifacts/runs/588db51c-1f85-41e4-bf7d-b26c0bf385a3/trace.fst`; run manifest saved as `artifacts/bio-sim-smoke.manifest.json`.
- Added SIMULATION mode to dashboard/API, with strict experiment allow-list and separate MOCK path. No arbitrary shell command input.
- Tests: `python3 -m unittest discover -s apps/host -v` — 9 passed including API flow and actual simulator adapter; `python3 -m py_compile apps/host/*.py` passed.
- No Zig or GTKWave installed. Dabao serial and BAOCHIP volume untouched; no hardware execution.

## 2026-11-12 — Blink, waveform inspection, React dashboard
- Verified upstream GTKWave official package metadata: Manjaro `extra` 3.3.128-1 provides FST reader/converter and FST examples. `sudo pacman -S --needed gtkwave` is awaiting user authentication; no package install confirmed yet.
- Installed upstream-tested Zig 0.15.2 into project-local `.venv` (not a system package). Built blink firmware with `-Demit-listing=false`; upstream default attempted optional objdump listing and failed because no RISC-V objdump is installed; retry passed and BIO errata check passed.
- Ran upstream `configs/blink.jsonc`; exit 0, cfginfo PASS, 10,000 cycles, observed repeated GPIO 21 transitions, genuine 107,364-byte FST.
- Added fixed allow-listed smoke/register-inspection/blink runs to the API adapter, with configuration contents/hash, upstream commit, Verilator/Zig versions, validation outcomes, duration, observed GPIO edge list, artifact size and downloadable FST endpoint.
- Saved reproducible manifests for smoke, register inspection, and blink under `artifacts/`; artifacts retained under `artifacts/runs/`.
- Replaced static dashboard frontend with React + TypeScript + Vite; `npm install` completed (68 packages, 0 reported vulnerabilities); `npm run build` passes. Backend serves production assets and retains API routes.
- Prepared Plus2 PlatformIO/Arduino project using official documented board target and M5Unified, with UI and versioned JSON serial frame source. Firmware not yet built/flashed and host serial bridge remains unconnected.
- Read-only Dabao udev confirmation: `/dev/ttyACM0`, VID/PID `1d50:6196`, serial `TLZ4A6`; by-id link confirmed. An additional `/dev/ttyACM1` is USB `1a86:55d4` CH9102-like USB Single Serial; not opened or asserted as M5Stick.
- Tests: 10 Python unit/API/simulation tests passed; py_compile passed; React TypeScript/Vite production build passed.

## 2026-11-12 — GTKWave, launcher, waveform evidence and protocol
- Verified `gtkwave --version`: GTKWave Analyzer 3.3.128; `/usr/bin/fst2vcd` and `/usr/bin/fstminer` present.
- Opened smoke, register-inspection, and blink FSTs in GTKWave. Each loaded successfully: FSTLOAD processed 13,485 facilities and built 5,001 signals / 8,484 aliases.
- Converted all three run FSTs with `fst2vcd`. Inspected blink `TOP.gpio_out[31:0]` and `gpio_dir`; bit 21 toggles repeatedly. FST edge times match log transitions with 1,429 ps trace origin offset.
- Added `/api/runs/{id}/waveform/open`, restricted to verified run-owned FSTs; added React Open in GTKWave action and missing-display/viewer/artifact error responses.
- Added `docs/WAVEFORMS.md` with reproducible GUI, CLI, and signal inspection instructions.
- Added host-side bounded/versioned JSON line parser and M5Stick request handler; no serial transport opened. Tests cover framing, fragmentation, invalid/oversized frames, hello, allowed mock run, and hardware-mode rejection.
- Read-only udev inventory still identifies Dabao at `/dev/ttyACM0`; separate `1a86:55d4` CH9102-style USB UART at `/dev/ttyACM1` is not enough to identify an M5Stick. No serial node opened, no BAOCHIP access.
- Final checks: 20 backend/API/simulator/protocol tests passed; Python compile passed; React/TypeScript Vite production build passed; all three FSTs converted successfully.
