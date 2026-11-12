# BIOScope Status

**Updated:** 2026-11-12
**Current milestone:** The pin-free FIFO0 probe succeeded once on physical Dabao and is recorded as `HARDWARE_VERIFIED`. The one-shot physical path is consumed and locked. The full dashboard/API startup and recorded result route are verified; this pass used read-only USB discovery and did not open serial ports. Bruce remains installed on the operator-correlated M5Stick and has no verified BIOScope protocol session.

## Verified working

- Official BIO-sim source at `7e9c9615e1c900c7ddae1c4645a87078b217abc3`; smoke, register inspection (`sfr_cfginfo == 0x10000408`) and blink pass in simulation.
- Blink simulation emits genuine FST; GPIO 21 transitions were correlated with logs and loaded in GTKWave.
- `experiments/bio/dabao_fifo_probe/main.c` compiled to a 20-byte RV32 BIO image using Zig 0.15.2 and the official BIO-sim translator/errata scan. BIO-sim loaded it, ran it, and read FIFO0 sentinel `0xb105c0de`; latest run `a3e804d5-88c2-4c95-9d6b-9da2120589e6` exit 0, `SIMULATED`, verified FST 62,484 bytes (SHA-256 `e85907c0bd539d14d8132165270e6365e12fd6a9417589efb5972803eac4de17`). This is simulator-only evidence.
- Current Dabao USB profile is matched using `1d50:6197`, product, unique serial, topology and interface-02 persistent by-id link. Older `6196` enumeration is historical. Xous version `v0.10.1-43-g8964027ff` is recorded in the physical run; no current-session serial interaction was performed.
- Official `bio-loader` (`a827a3c944c44c1b507e4eab55c76fc67871a8ca`) and Xous `bio.rs` source establish a physical BIO loader and FIFO receive command. The approved run below confirms one successful FIFO0 response; the prior BIO image has no verified backup/readback path.
- Hardware requests use strict state vocabulary and an allow-listed experiment. The one fixed physical probe is now consumed; no API/dashboard hardware execution is enabled. No GPIO operation is claimed.
- Host API and React/TypeScript/Vite dashboard expose experiment runs, logs, manifests, validation and artifacts.
- M5Stick Plus2 BIOScope firmware compiles with the documented PlatformIO target (compile-only; it was not flashed).
- New USB profile matcher uses VID/PID + USB serial + USB topology and exact `/dev/serial/by-id` link. The dashboard has a separate Hardware Devices page and polls device inventory every 2 seconds.
- New tests cover exact-profile match, VID/PID-only rejection, topology mismatch, USB presence with inaccessible serial link, and disconnect/reconnect transitions. Device API timestamps describe current-process history and reset after host restart.
- Bruce serial workflow researched from official documentation. The documented `info` command at 115200 8N1 was not sent: Linux CDC ACM/TTY opening asserts DTR/RTS, PySerial applies line states after open, and ModemManager is active. Reset-free opening cannot be guaranteed, so the fail-closed bridge never constructs a serial object.
- Full M5Stick integration assessment and a preserve-Bruce/recovery proposal are documented in `docs/M5STICK_FIRMWARE_CHANGE_PROPOSAL.md`.
- Xous USB console/build documentation reviewed. Boot1 serial console can accept commands and update files; active stage is unverified, so console remains unopened.

## Historical sandbox visibility before the physical run

The latest read-only scan in this agent's sandbox sees Dabao `1d50:6197`, product `Dabao`, serial `[Dabao serial redacted]`, topology `1-4`, and the M5Stick-associated bridge `1a86:55d4`, serial `[M5Stick bridge serial redacted]`, topology `1-3`. It cannot see `/dev/serial/by-id` or tty nodes in this execution environment, so the API reports serial links unavailable here. M5Stick identity is operator-correlated; descriptor evidence alone identifies its QinHeng bridge, not the M5Stack board model. No port was opened.

## Current safety state

- Bruce firmware remains installed and untouched. No flash, erase, reset or serial command was performed.
- The Dabao CDC port was opened once for the separately approved fixed FIFO probe, then closed. No port was opened during this final integration/readiness pass; BIOScope changed no DTR/RTS state in this pass.
- The mounted BAOCHIP volume remains untouched. No firmware or bootloader write occurred.
- No M5Stick protocol session exists: Bruce does not implement BIOScope JSON hello. The local BIOScope bridge is not to be run against Bruce.

## Latest validation

- Backend: all 44 tests passed, including target state-machine and safe-version-query tests.
- Frontend: `npm run build` passed (TypeScript `tsc -b` and Vite production build; 29 modules bundled).
- Python compilation of host and helper scripts and `git diff --check` passed.
- Existing genuine manifests verify smoke and register inspection at exit 0 with `cfginfo_pass`; blink exit 0 with `gpio21_transitions`, 65 `gpio_out[21]` edges and its verified 107,364-byte FST. GTKWave/FST inspection was previously verified and is documented in `docs/WAVEFORMS.md`.
- No screenshot is archived: headless Firefox attempts returned API-offline/blank captures, which were discarded instead of being presented as evidence.
- Hardware integration tests use temporary sysfs/by-id fixtures; they do not access hardware serial devices.

See [device discovery and safe integration](../docs/DEVICE_DISCOVERY.md), [hardware integration](../docs/HARDWARE_INTEGRATION.md), [architecture](../docs/ARCHITECTURE.md), and [demo runbook](../docs/DEMO.md).

## Historical blockers before physical probe (superseded where noted)

- The current Dabao Xous/console version has not been queried. Opening USB CDC may change control-line state; reset-free behavior is not verified.
- A fixed, one-shot read-only version-query script is prepared and uses only documented `ver xous`; it opens only the exact Dabao profile, requests DTR/RTS low and sends no retries. Running it requires explicit approval because CDC open can still reset the board and current user does not have `uucp` permissions.
- The documented loader overwrites the previously stored BIO program in keystore; existing program backup/readback is unsupported by the inspected console source.
- Linux tty is `root:uucp` mode 0660; current user is not in `uucp`. No group, udev, permission, or sudo change has been made.
- To run the real probe, the operator must explicitly approve the exact serial open + 1,000,000 baud BIO upload/pad/reload + `bio rx 1 5` operation. Until then evidence stays NOT RUN for hardware.

## 2026-11-12 — Exact Xous protocol verified; physical write approval pending

- Operator supplied successful version output `Xous version: v0.10.1-43-g8964027ff`; exact source revision `8964027fff25f8b85d3d3c63933d365ac7614523` was fetched and `apps-dabao/dabao-console/src/cmds/bio.rs` inspected. Earlier status lines above are historical and superseded for version-query status only.
- Added `apps/host/dabao_adapter.py` with exact identity checks, serialized device lock, 70-byte chunk framing/CRC32, fixed command sequence, bounded waits, one FIFO read, close handling, and run manifest/stdout/stderr/hardware result artifacts. Added `scripts/run-dabao-fifo-probe.py`; the one-shot gate is now consumed by the published hardware evidence and refuses future attempts before USB discovery.
- Verified source and binary hashes against the 20-byte build manifest. No GPIO calls. A full commit writes the 0xF00-byte Xous keystore image: 20 bytes + 44 bytes padding in the first chunk and 59 zero chunks. Existing stored BIO image has no verified readback or recovery path; `bio reload` also reapplies the existing, unreadable pin configuration.
- Fake-serial tests cover framing/CRC, exact target rejection, approval gating, single FIFO request, matching result, and timeout cleanup. Targeted command from `apps/host`: `python3 -m unittest test_dabao_fifo_probe test_dabao_hardware -v` — 14 tests passed; Python compilation of adapter/state model/runner passed. These tests did not open hardware.
- No physical upload/run, dashboard hardware execution, screenshot, or hardware evidence has occurred. Awaiting the exact operator approval below; after verified FIFO response, wire the run into the API/dashboard and capture genuine evidence.
- Latest full backend validation: `python3 -m unittest discover -s apps/host -v` — 49 passed, 1 skipped because the sandbox denies local socket bind. `git diff --check` and targeted Python compilation passed.

## 2026-11-12 — First physical Dabao BIO run verified

- Operator executed the approved one-time CLI on Dabao [Dabao serial redacted]. Output: state `HARDWARE_VERIFIED`, evidence `HARDWARE_VERIFIED`, expected FIFO0 `0xB105C0DE`, actual `0xB105C0DE`, match true, exit 0. Run ID `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`; start `2026-11-12T10:12:31.886Z`; duration 0.2958 seconds. Physical write/reload happened once; no retry.
- Saved original run manifest, console stdout/stderr and `hardware-result.json` in that run directory. Console log includes the Xous `b105c0de` line, `BIO load successful`, final `OK` and port-close record. Target Xous: `v0.10.1-43-g8964027ff`; exact source commit: `8964027fff25f8b85d3d3c63933d365ac7614523`.
- The generated operation text misstated 63 padded chunks; the exact 0xF00-byte BIO region contains 60 chunks total, so 59 chunks are zero-filled after chunk 0. The original root-owned run files remain unchanged. Added a checksum-bound amendment and integrity index at `docs/hardware-evidence/d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62-amendment.json`; the API applies its wording correction in memory only after verifying the original manifest SHA-256.
- Integrated the historical physical result into read-only API history/capabilities and the experiment catalog. Dashboard displays the physical run separately from simulation. `HARDWARE` requests are disabled in the dashboard and rejected by the API; only the fixed CLI could perform this state-changing operation. No additional serial action was run.
- Hardened the fixed CLI after success: it now refuses to start if any prior `HARDWARE` attempt for this probe is recorded, including a failed/ambiguous attempt. It stops before discovery/serial open; a repeat requires a separately reviewed software change and new approval.
- Final backend suite: `python3 -m unittest discover -s apps/host -v` — 52 passed, no skips. This includes the real run history/API response, artifact download, refusal of dashboard/API hardware execution, and one-shot CLI retry blocking.
- Final Python compilation and `git diff --check` passed. Dashboard TypeScript/Vite production build passed: 29 modules bundled. API integration tests now bind an ephemeral localhost port successfully in this run.
- Genuine GUI screenshot remains unarchived: headless browser captures either showed API-offline state or a blank frame and were discarded. No screenshot is claimed as physical evidence. No firmware flash, BAOCHIP-volume access, M5Stick communication, or Git push occurred.

## 2026-11-12 — Public evidence and demo readiness

- Created a sanitized public copy of the physical run artifacts; serials, topology, local tty/by-id paths, prior approval phrase and echoed Base64 payload are redacted. Public-copy checksums and raw-manifest provenance verified; original run files remain unchanged.
- The one-shot runner now checks the published physical evidence manifest and refuses a repeat before USB discovery. HTTP hardware execution remains disabled.
- Added Getting Started, demo video guide, and readiness assessment. README and hardware/demo documentation point to the exact physical run and separate simulation, recorded hardware, and Bruce limitations.
- Live API and Vite dashboard started. Health/capabilities/device/catalog/history/artifact/FST routes and the Vite `/api` proxy returned HTTP 200. Dabao and M5Stick-associated USB bridge were both connected; both serial ports reported unopened.
- Final checks: 55 backend tests passed; Python compilation passed; React/TypeScript/Vite production build passed (29 modules); public evidence integrity/privacy scan passed; `git diff --check` passed after the final edits.
- No screenshot is archived. No serial command, hardware rerun, firmware update, M5Stick communication, or BAOCHIP-volume access occurred in this readiness pass.
