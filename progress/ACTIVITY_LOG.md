# Activity Log

## 2026-11-12 — Final hardware safety preflight and validation
- Rechecked the connected board profiles from read-only `/api/devices`: Dabao `1d50:6196`, serial `TLZ4A6`, topology `1-4`, `/dev/ttyACM0`; M5Stick operator-associated USB bridge `1a86:55d4`, serial `5B1E046678`, topology `1-3`, `/dev/ttyACM1`, with the expected persistent by-id link. The M5Stick descriptors identify a QinHeng USB serial bridge, not the board model. `serial_opened` was false for both profiles.
- Inspected PySerial 3.5 open behavior and Linux `cdc_acm`/TTY line-control implementation. Opening can assert DTR/RTS; PySerial applies its requested states after open. ModemManager was active and the M5Stick CDC device was a candidate. The documented Bruce `info` command at 115200 8N1 was not sent because reset-free opening could not be established. No port was opened, no line was toggled, and Bruce remains untouched.
- Hardened `m5stick_bridge.py` to require full profile/persistent-path/pyserial descriptor match, then fail closed before creating a physical serial object. Protocol-v1 mock transport uses bounded JSON frames, requires hello, validates exact run-request fields, and routes only catalog experiment IDs and approved SIMULATION/MOCK modes. Added tests for extra/malformed fields, identity mismatch, timeouts, disconnects, and proof that physical serial construction is never attempted.
- Updated architecture, safety, README, Bruce assessment, device discovery, demo and status docs. Clarified process-local connection timestamps and the reason no Bruce `info` response exists.
- Revalidated simulator manifests: smoke and register inspection exit 0 with `sfr_cfginfo == 0x10000408` and verified 46,301-byte FSTs; blink exit 0 with 65 recorded GPIO 21 output edges and verified 107,364-byte FST. Upstream revision `7e9c9615e1c900c7ddae1c4645a87078b217abc3`.
- Final backend suite: 33 tests passed. TypeScript/Vite production build passed; Python compilation and `git diff --check` passed. No hardware execution was performed.
- Tried headless Firefox screenshot capture as requested; captures showed API offline or blank even when the local API was running in a separate execution context. Discarded all such images; screenshot index records none rather than presenting false evidence.
- No Git commit/push, package install, serial open, firmware write, or BAOCHIP volume access occurred.

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

## 2026-11-12 — Profile-based hardware inventory and dashboard
- Added read-only USB profile discovery in `apps/host/device_discovery.py`; identifies Dabao and the operator-correlated M5Stick bridge only when VID/PID, USB serial, and recorded topology all match. It separately checks the exact `/dev/serial/by-id` link and live tty node.
- Added sysfs interface/driver enumeration and an API response that distinguishes USB presence from serial-link availability. No tty device is opened.
- Added a dedicated Hardware Devices dashboard page with two separate cards, identity confidence, topology, persistent path, driver, safety state and two-second refresh. M5Stick explicitly displays bridge-only descriptor confidence; Dabao and M5Stick states are independent.
- Added 5 discovery tests covering exact match, VID/PID-only rejection, topology mismatch, inaccessible by-id links and disconnect/reconnect state transitions.
- Reviewed official Bruce serial docs: 115200 8N1 and broad documented command interface, including `info`/`uptime`/`free` plus state-changing transmit, GPIO, storage, power and reset commands. BIOScope's protocol-v1 bridge is incompatible with Bruce; no communication attempted. Bruce remains installed.
- Reviewed official Xous USB boot1 console docs. The console accepts commands/update traffic; active stage is not verified. Dabao serial and BAOCHIP volume were not accessed.
- Initial sandbox run: 28 backend tests, 27 passed, local-socket API test skipped by sandbox socket policy; TypeScript/production Vite build passed.
- Sandbox can see both USB sysfs profiles but does not expose `/dev/serial/by-id` or `/dev/ttyACM*`; UI now reports this as a serial-link visibility issue separately from hardware presence.
- Approved non-sandbox rerun: all 28 backend tests passed, including API-to-device-inventory integration. Final TypeScript/Vite production build passed. Headless screenshot capture was discarded because Firefox could not load the local API data; see `docs/screenshots/README.md`.
- Added a Plus2 Bruce-preservation and firmware replacement/recovery proposal. M5Stack factory restore is documented as a fallback to factory firmware, not as a Bruce backup; no firmware upload/readback was attempted.

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

## 2026-11-12 — Plus2 build and safe serial bridge preparation
- Installed PlatformIO 6.2.0 and dependencies only in the project `.venv`/`.cache/platformio`.
- Built Plus2 target successfully with PlatformIO Espressif32 6.7.0, Arduino core 2.0.16, Xtensa 8.4.0+2021r2-patch5, M5Unified pinned to `96576a14247ddc935149145aa6b51943464120f1`, ArduinoJson 7.4.3. Final firmware `.bin` is 525,856 bytes; compile only, not flashed.
- Added reproducible `scripts/build-m5stick.sh`, pinned dependencies, and firmware build instructions.
- Added explicit M5 serial bridge CLI requiring port + exact USB serial, verifying VID/PID before opening, setting DTR/RTS low, requiring protocol-v1 hello, and routing allow-listed requests to the same experiment engine. Added mock transport integration tests; actual device port remains unopened.
- Read-only descriptor inventory still shows Dabao `/dev/ttyACM0` (1d50:6196, TLZ4A6) and generic CH9102 `/dev/ttyACM1` (1a86:55d4, serial 5B1E046678). The CH9102-to-board relationship is unknown.
- Reviewed Xous Baochip README, Dabao apps README, boot-chain docs and USB console source notes. Console is command/update capable; active boot stage is not verified. No serial session attempted; BAOCHIP volume untouched.

## 2026-11-12 — Final hardware preflight
- Rebuilt Plus2 firmware with pinned PlatformIO environment using `scripts/build-m5stick.sh`: SUCCESS. Binary SHA-256 `597c356689f924d57e4926cc11d606e7431f33cafa4748335bbc5b4b0da58224`, 525,856 bytes; compile-only.
- Added exact build workflow, pinned M5Unified commit and ArduinoJson 7.4.3. PlatformIO and pyserial remain project-local; no global packages changed.
- Completed explicit M5 serial bridge: identity precheck (CH9102 VID/PID and exact USB serial), DTR/RTS low, protocol v1 hello gate, bounded JSON line parser, run request allow-list and shared simulation/mock execution engine. Mock transport verifies hello → run → status/result frames; no physical port opened.
- Official Xous docs confirm Dabao USB console and bootloader channel can accept commands/updates. With the currently running stage unknown, BIOScope cannot certify passive read-only access; console remains unopened.
- Final checks: 23 backend/API/simulation/protocol tests passed; Python compile passed; Vite production build passed; PlatformIO build passed.
