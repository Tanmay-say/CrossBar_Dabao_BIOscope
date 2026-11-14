# Activity Log

## 2026-11-12 — First physical Dabao BIO FIFO0 probe

- Operator ran the exact approved command once on Dabao [Dabao serial redacted]. Returned run `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`, `HARDWARE_VERIFIED`, exit 0; expected and actual FIFO0 both `0xB105C0DE`. Duration recorded as 0.2958 seconds.
- The supplied CLI output and the saved raw run files were checked. `stdout.log` contains the Xous `b105c0de` record, loader success, FIFO `OK`, and host close. `hardware-result.json` and manifest identify VID/PID `1d50:6197`, serial `[Dabao serial redacted]`, topology `1-4`, the operator-reported Xous version and exact commit, source and binary SHA-256 values, and operation sequence. No additional hardware command was sent.
- Corrected an inaccurate descriptive chunk count in API presentation using a checksum-bound amendment under `docs/hardware-evidence/`; preserved original root-owned run files unchanged. The pinned source pads 59 chunks after chunk 0, not 63.
- Added read-only physical run presentation to host history and capability API, exposed logs/result/manifest/amendment as verified downloads, and added the physical probe to the catalog. Hardware mode stays manually gated; API submissions are rejected and no re-run endpoint invokes serial.
- Updated overview and run-detail UI to distinguish physical result from SIMULATION/MOCK, display run identity and FIFO0 match, and expose actual logs and manifest. Updated README, architecture, hardware integration, demo, screenshot index, status and evidence index.
- Targeted backend tests: 29 passed, 1 skipped because sandbox local socket bind is denied. Dashboard production build (TypeScript/Vite) passed. Live API route was read outside the sandbox and returned the hardware-verified record. Headless screenshot attempts were API-offline/blank; discarded, no screenshot claim. BAOCHIP volume, firmware and M5Stick were untouched; nothing pushed.
- Final verification after read-only API/dashboard integration: full backend suite 52/52 passed, including live HTTP lookup of this physical run, console output, integrity amendment downloads, HTTP 403 for further hardware execution, and retry blocking. `python3 -m py_compile apps/host/*.py scripts/*.py`, `git diff --check`, and final React/TypeScript/Vite build passed (29 modules). No dashboard write endpoint can repeat the operation.
- Added a one-shot attempt guard to the physical CLI after confirming its approval phrase would otherwise remain reusable. Any recorded hardware attempt for this catalog probe now blocks before USB discovery/serial open. This does not alter or rerun the completed hardware result.

## 2026-11-12 — Final hardware safety preflight and validation
- Rechecked the connected board profiles from read-only `/api/devices`: Dabao `1d50:6196`, serial `[Dabao serial redacted]`, topology `1-4`, `/dev/ttyACM0`; M5Stick operator-associated USB bridge `1a86:55d4`, serial `[M5Stick bridge serial redacted]`, topology `1-3`, `/dev/ttyACM1`, with the expected persistent by-id link. The M5Stick descriptors identify a QinHeng USB serial bridge, not the board model. `serial_opened` was false for both profiles.
- Inspected PySerial 3.5 open behavior and Linux `cdc_acm`/TTY line-control implementation. Opening can assert DTR/RTS; PySerial applies its requested states after open. ModemManager was active and the M5Stick CDC device was a candidate. The documented Bruce `info` command at 115200 8N1 was not sent because reset-free opening could not be established. No port was opened, no line was toggled, and Bruce remains untouched.
- Hardened `m5stick_bridge.py` to require full profile/persistent-path/pyserial descriptor match, then fail closed before creating a physical serial object. Protocol-v1 mock transport uses bounded JSON frames, requires hello, validates exact run-request fields, and routes only catalog experiment IDs and approved SIMULATION/MOCK modes. Added tests for extra/malformed fields, identity mismatch, timeouts, disconnects, and proof that physical serial construction is never attempted.
- Updated architecture, safety, README, Bruce assessment, device discovery, demo and status docs. Clarified process-local connection timestamps and the reason no Bruce `info` response exists.
- Revalidated simulator manifests: smoke and register inspection exit 0 with `sfr_cfginfo == 0x10000408` and verified 46,301-byte FSTs; blink exit 0 with 65 recorded GPIO 21 output edges and verified 107,364-byte FST. Upstream revision `7e9c9615e1c900c7ddae1c4645a87078b217abc3`.
- Final backend suite: 33 tests passed. TypeScript/Vite production build passed; Python compilation and `git diff --check` passed. No hardware execution was performed.
- Tried headless Firefox screenshot capture as requested; captures showed API offline or blank even when the local API was running in a separate execution context. Discarded all such images; screenshot index records none rather than presenting false evidence.
- No Git commit/push, package install, serial open, firmware write, or BAOCHIP volume access occurred.
- After the above validation, committed the reviewed implementation as `8b1ec97` (`Complete BIOScope hardware safety integration`) and pushed it to `origin/main` for the submission. The BIO-sim submodule working tree was not included.

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
- Confirmed `BAOCHIP` mounted at `mounted BAOCHIP volume`; left volume contents untouched. Did not open `/dev/ttyACM0`.
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
- Read-only Dabao udev confirmation: `/dev/ttyACM0`, VID/PID `1d50:6196`, serial `[Dabao serial redacted]`; by-id link confirmed. An additional `/dev/ttyACM1` is USB `1a86:55d4` CH9102-like USB Single Serial; not opened or asserted as M5Stick.
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
- Read-only descriptor inventory still shows Dabao `/dev/ttyACM0` (1d50:6196, [Dabao serial redacted]) and generic CH9102 `/dev/ttyACM1` (1a86:55d4, serial [M5Stick bridge serial redacted]). The CH9102-to-board relationship is unknown.
- Reviewed Xous Baochip README, Dabao apps README, boot-chain docs and USB console source notes. Console is command/update capable; active boot stage is not verified. No serial session attempted; BAOCHIP volume untouched.

## 2026-11-12 — Final hardware preflight
- Rebuilt Plus2 firmware with pinned PlatformIO environment using `scripts/build-m5stick.sh`: SUCCESS. Binary SHA-256 `597c356689f924d57e4926cc11d606e7431f33cafa4748335bbc5b4b0da58224`, 525,856 bytes; compile-only.
- Added exact build workflow, pinned M5Unified commit and ArduinoJson 7.4.3. PlatformIO and pyserial remain project-local; no global packages changed.
- Completed explicit M5 serial bridge: identity precheck (CH9102 VID/PID and exact USB serial), DTR/RTS low, protocol v1 hello gate, bounded JSON line parser, run request allow-list and shared simulation/mock execution engine. Mock transport verifies hello → run → status/result frames; no physical port opened.
- Official Xous docs confirm Dabao USB console and bootloader channel can accept commands/updates. With the currently running stage unknown, BIOScope cannot certify passive read-only access; console remains unopened.
- Final checks: 23 backend/API/simulation/protocol tests passed; Python compile passed; Vite production build passed; PlatformIO build passed.

## 2026-11-12 — Dabao physical BIO source trace and pin-free probe

- Re-read current official BIO-sim requirements and traced its named physical loader to `baochip/bio-loader`; acquired source read-only in `/tmp/bio-loader-inspect`, exact revision `a827a3c944c44c1b507e4eab55c76fc67871a8ca`. Inspected loader implementation and Xous `apps-dabao/dabao-console/src/cmds/bio.rs`.
- Source confirms official upload protocol is a 1,000,000-baud serial stream of 64-byte chunks with CRC, plus `bio pad` for zero fill and `bio reload`. Xous writes code and validity marker to application keystore, initializes BIO, then starts the core. `bio rx <count> <timeout-seconds>` reads FIFO0 and logs the returned word. Loader port-open does not override DTR/RTS; unit-specific CDC reset effect and installed Xous app version remain unknown.
- Read-only runtime identity: Dabao `1d50:6197`, product `Dabao`, serial `[Dabao serial redacted]`, topology `1-4`, CDC ACM interface 02, persistent link `/dev/serial/by-id/[redacted Dabao persistent path]`. Historical `6196` profile retained, not conflated. No USB storage interface in current descriptor snapshot. `/dev/ttyACM0` remains unopened; BAOCHIP filesystem not accessed.
- Added `experiments/bio/dabao_fifo_probe/main.c`, a no-GPIO single-word FIFO0 program, and reproducible `scripts/build-dabao-bio-probe.py`. Command `python3 scripts/build-dabao-bio-probe.py` exited 0. Zig 0.15.2; official translator/post-link errata check PASS. Binary: 20 bytes, SHA-256 `cfc0502faf630bae4088e06131f23594d1b14928549743eb774d396b88e6b69b`; build evidence remains `COMPILE_ONLY`.
- Added `dabao-fifo-probe` to the fixed catalog as SIMULATION/MOCK only. Latest API run `a3e804d5-88c2-4c95-9d6b-9da2120589e6`: exit 0, 2,000 cycles, cfginfo check PASS, FIFO0 returned `0xb105c0de`, real FST 62,484 bytes, SHA-256 `e85907c0bd539d14d8132165270e6365e12fd6a9417589efb5972803eac4de17`; evidence `SIMULATED`, not hardware. Config uses project-relative binary and FST paths; run manifest captures its SHA-256.
- Added strict current Dabao descriptor matching (`6197`, product, serial, topology, by-id interface) while keeping the prior `6196` enumeration as a separate historical variant. Added `/api/hardware/capabilities`; dashboard describes upstream-supported path, unknown device app version and upload side effects, with physical execution disabled.
- Inspected a sparse official Xous source snapshot at `99bbfcc15320561f09a97e9ebb5e05a673ca3379`: `dabao-console` registers the `bio` command, the API/HAL exposes core initialization/resource operations, the app stores BIO code in keystore slot indices 3–122, and `ver xous` is read-only. A Xous target build was not attempted because `cargo`, `rustc`, and `rustup` are not installed; no Rust toolchain was installed.
- Added a fixed one-shot `scripts/dabao-readonly-version.py` that validates current USB+by-id+tty ancestry, exclusively opens only the Dabao CDC profile, requests DTR/RTS low, sends one `ver xous` command and closes. Fake-transport tests verify one command/no retry and close. It has not been run: USB CDC opening may still reset the board, and the tty is `root:uucp` 0660 while the active user lacks `uucp` access.
- Added hardware request state model/allow-list and tests proving request planning is non-executing, transitions are guarded, `HARDWARE_VERIFIED` requires an actual matching target response, and identity mismatch is rejected. No physical execute endpoint, serial opens, M5Stick communication, firmware writes, BAOCHIP volume access, package installation, or Git push occurred.
- Full backend run after integration changes: one initial run exposed a M5 profile fallback regression after tightening Dabao matching; corrected it and reran all 41 successfully. A later 44-test run exposed a fake-transport test fixture omission; corrected the fixture and reran all 44 successfully. The final API test submits the pin-free probe through HTTP and validates the downloaded genuine FST.
- Final checks: `python3 -m py_compile apps/host/*.py scripts/build-dabao-bio-probe.py scripts/dabao-readonly-version.py` exit 0; dashboard `npm run build` exit 0 (TypeScript and Vite, 29 modules); `git diff --check` exit 0.
- Final read-only profile scan sees both USB descriptors but this agent's sandbox cannot see their `/dev/serial/by-id` links or tty nodes. The host API reports USB presence separately from serial-link visibility. No serial or update-volume access occurred.
# 2026-11-12 — Exact Xous BIO protocol and gated physical probe preparation

- Operator reported successful version query: `Xous version: v0.10.1-43-g8964027ff`. Fetched exact Xous revision `8964027fff25f8b85d3d3c63933d365ac7614523` and inspected its `apps-dabao/dabao-console/src/cmds/bio.rs`; do not infer protocol compatibility from another revision.
- Verified commands and responses: `bio ready` -> `OK`; a Base64 string decoding to 70 bytes (BE chunk index + 64 data + BE CRC32) -> `OK`; `bio pad` -> `SUCCESS`, commits padded 0xF00 bytes to application keystore; `bio reload` -> `BIO load successful`; `bio rx 1 5` -> logs FIFO0 data and returns `OK`. The receive command logs timeout but still reads the FIFO register, so host performs one receive and validates the actual sentinel text.
- The 20-byte compiled image matches build manifest hashes and has no GPIO instructions. Program effect is one FIFO0 write of `0xB105C0DE` then wait. Full padded image has 44 zeros after the code in chunk 0 and 59 zero chunks. Existing stored image cannot be read back through documented console commands; upload overwrites it. Existing pin settings are also unreadable and are reapplied by reload. These are material risks presented before approval.
- Added a constrained host uploader, exact identity revalidation, lock, bounded protocol handling, manifest/log capture, strict approval phrase CLI, and fake transport tests. Targeted test command from `apps/host`: `python3 -m unittest test_dabao_fifo_probe test_dabao_hardware -v` exited 0 (14 tests); `py_compile` exited 0. No serial port was opened by these tests and no physical BIO command was sent.
- Physical execution is pending explicit approval for the exact Dabao target and operation. No dashboard hardware execution or screenshot is claimed yet.

## 2026-11-12 — Physical FIFO0 evidence publication and demo readiness

- Recorded the operator-authorized physical Dabao run `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`: expected FIFO0 `0xB105C0DE`, actual `0xB105C0DE`, Xous `v0.10.1-43-g8964027ff`. The one-shot overwrote the prior stored BIO image; it was not repeated.
- Audited the original local run without modifying it, prepared sanitized public evidence and a redaction amendment, and verified file sizes/SHA-256 values against `docs/hardware-evidence/public/integrity.json`. No credentials, host-local paths, tty/by-id paths, USB serials, approval phrase, or echoed Base64 payload are present in the sanitized public evidence copy.
- Disabled the one-shot runner after the verified operation and retained explicit no-retry behavior. The dashboard/API exposes the historic hardware result but does not expose a physical execution route.
- Started the actual API and Vite development server for live checks. Health, capability, device, experiment catalog, history, hardware-run artifacts, blink FST and Vite `/api` proxy returned HTTP 200. Read-only discovery reported Dabao and the operator-associated M5Stick USB bridge; both reported `serial_opened: false`. No port was opened and no hardware command was sent.
- Production API assets and the Vite page loaded successfully. GTKWave 3.3.128 is available; the existing genuine blink FST is served at 107,364 bytes. No screenshot is archived or claimed.
- Validation: 55 backend tests passed; Python compilation passed; TypeScript/Vite production build passed; `git diff --check` passed. Device and Bruce limitations plus exact demo startup instructions are documented in `docs/DEMO_READINESS.md`, `docs/GETTING_STARTED.md`, and `docs/DEMO_VIDEO_GUIDE.md`.
# 2026-11-12 — PulseLink first two-board experiment implementation

- Added `pulselink_signal_generator`: pin-free in the sense of no unrelated pin operations; it configures BIO pin 1/PB1 as an output, drives LOW, emits ten HIGH/LOW cycles using 3,500 waits at 7 kHz quantum setting, then holds LOW. Built with upstream BIO-sim revision `7e9c9615e1c900c7ddae1c4645a87078b217abc3`; output image 58 bytes, SHA-256 `22db6c3980ff91f0d953b27180d0823abce9276a8e1391f13266365f2a412c3e`. Build command `./.venv/bin/python scripts/build-pulselink-bio.py`, exit 0; classification `COMPILE_ONLY`.
- Ran the real BIO-sim RTL using the new script. Run `pulselink-sim-25a8ed17-f063-40d2-9dc9-86aa8b7bdae0`, exit 0: ten rising and ten falling GPIO1 transitions, nominal one-second period, final LOW. FST `artifacts/runs/pulselink-sim-25a8ed17-f063-40d2-9dc9-86aa8b7bdae0/trace.fst`, 27,539,466 bytes, SHA-256 `aa604817141885f8e23b389fe10a230f1ce2ee1748393c68312b8d22f25de5c7`; classification `SIMULATED`, not physical.
- Replaced the prepared Plus2 demo source with a GPIO32 receiver/UI, edge interrupt capture, actual period-derived frequency, reset/page buttons, and bounded newline JSON protocol v1. `scripts/build-m5stick.sh` exit 0 using PlatformIO; firmware image compiles but was not flashed. Bruce preserved.
- Added strict telemetry parsing/state tracking, disconnect/reconnect handling, complete-capture validation, GPIO32 edge VCD and hardware-evidence manifest generation, opt-in serial service and PulseLink dashboard view. No M5Stick serial port was opened and no real telemetry was received. A test first revealed that an early edge queue overflow could be forgotten before completion; capture-wide overflow tracking now prevents VCD completion in that case.
- Updated `docs/PULSELINK.md`, `docs/PULSELINK_WIRING.md`, `docs/PULSELINK_DEMO.md`, README, architecture/safety requirements and this status log. Pin mapping references the official Dabao and Plus2 docs; the Dabao waveform still requires approved unloaded voltage measurement before wiring.
- Validation: final backend suite `python3 -m unittest discover -s apps/host -v` completed 63 tests OK with local loopback permitted; `python3 -m py_compile apps/host/*.py` exit 0; dashboard `npm run build` exit 0 (TypeScript and Vite, 29 modules); PlatformIO build exit 0; BIO compiler/translator exit 0; `git diff --check` exit 0. Physical upload/run, M5Stick flash, wiring, live serial, and continuous GTKWave streaming were not attempted.

## 2026-11-12 — Operator authorized physical PulseLink staging

- Re-ran read-only discovery immediately before physical operation. Exact profiles matched the expected VID/PID, product/bridge identity, USB serial, topology and persistent by-id link for Dabao TLZ4A6 on `1-4` and operator-correlated M5Stick bridge 5B1E046678 on `1-3`; both serial-open flags were false.
- Attempted the authorized PlatformIO upload command to the exact M5Stick by-id path. `sudo` returned “a terminal is required to read the password” and then “a password is required”; PlatformIO never started and no USB serial device was opened. No firmware change occurred. Operator must run the command in an interactive terminal.
- Audited pinned Xous `bio.rs`: `bio pin 1` and `bio clk 7000` each persist settings and return `OK`; `bio <base64>` stages indexed 64-byte data with big-endian CRC32; `bio pad` fills/commits the 0xF00-byte image and returns `SUCCESS`; `bio reload` initializes/starts the core. Therefore PulseLink staging intentionally omits `bio ready` and `bio reload`.
- Added `apps/host/dabao_pulselink.py` and `scripts/prepare-pulselink-dabao.py`, which revalidate target and build hash, perform only the authorized config/stage/commit sequence, log a preparation manifest, and never start the program. Three fake-transport tests pass, including identity mismatch preventing port open. The helper has not been run on hardware.
- Updated PulseLink and demo docs with exact commands and current sudo blocker. No serial communication, flash, BIO configuration write, wiring, run, GTKWave physical trace or Git push occurred.
