# BIOScope demo readiness

Assessment date: 2026-11-12.

## Readiness summary

**Demo-ready for a truthful software + recorded hardware demonstration. Not ready for a live M5Stick operator session or a new physical Dabao run.** The Dashboard/API can display existing run evidence and simulation artifacts; no additional hardware operation is required for the demo described here.

| Capability | Status | Evidence / limit |
|---|---|---|
| Python host API and React/Vite dashboard | VERIFIED | API and Vite development server routes are tested during this readiness pass; startup commands are in `GETTING_STARTED.md`. |
| BIO-sim smoke and register/config inspection | SIMULATION ONLY | Upstream BIO-sim results; no physical silicon claim. |
| BIO-sim blink and FST/GPIO 21 transitions | SIMULATION ONLY | Genuine FST under local `artifacts/runs`; GTKWave workflow documented in `WAVEFORMS.md`. |
| Dabao identity discovery | VERIFIED | Read-only sysfs/by-id matching; runtime inventory does not open the port. |
| Dabao BIO FIFO0 result | VERIFIED | Run `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`; expected and actual FIFO0 are both `0xB105C0DE`; result provenance and sanitized public copies are indexed under `hardware-evidence/`. |
| Live Dabao BIO execution from dashboard | BLOCKED | Physical execution API is disabled. The documented loader overwrites the stored BIO image; the prior image has no verified readback/recovery. Do not repeat the probe. |
| M5Stick USB bridge discovery | VERIFIED | Read-only USB identity/association; descriptors identify the USB-UART bridge, not independently the M5Stick model. |
| M5Stick BIOScope communication | BLOCKED | Bruce is preserved. Its documented interface is not verified to support BIOScope's JSON protocol; no serial communication is attempted. |
| BIOScope Plus2 firmware build | WORKING — NOT PHYSICALLY VERIFIED | Source compiled for the Plus2 previously; it was not flashed or run on hardware. |
| Dashboard screenshot proof | PARTIAL | No screenshot is archived. Previous headless captures were empty/offline and discarded; no screenshot is claimed. |
| BIO-sim source checkout and toolchain | VERIFIED | Pinned upstream revision and local toolchain are recorded in `TOOLCHAIN_PLAN.md`. |

## Physical evidence

- Run ID: `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`.
- Target: Baochip-1x Dabao; Xous `v0.10.1-43-g8964027ff`, source revision `8964027fff25f8b85d3d3c63933d365ac7614523`.
- Expected: FIFO0 `0xB105C0DE`.
- Captured: FIFO0 `0xB105C0DE`.
- Classification: `HARDWARE_VERIFIED`; this is a completed historical run, not a fresh test in this session.
- The physical probe used no pin instructions and did not verify GPIO pads, external wiring, or electrical behavior.
- The stored BIO image was replaced by the approved probe. No documented image backup is available. The BAOCHIP update volume was not accessed.

## Software checks

Validated on 2026-11-12:

- Backend: `./.venv/bin/python -m unittest discover -s apps/host -v` — **55 passed**.
- Python: `./.venv/bin/python -m py_compile apps/host/*.py scripts/*.py` — passed.
- Frontend: `npm ci` — completed with 0 reported vulnerabilities; `npm run build` — TypeScript check and Vite production build passed (29 modules).
- Live API: health, hardware capabilities, devices, catalog, run history, physical manifest/result/logs and blink FST returned HTTP 200. Both USB profiles were connected; each reported `serial_opened: false`.
- Dashboard: Vite page and `/api/health` proxy both returned HTTP 200.
- Evidence audit: public artifact checksums and source-manifest provenance passed; privacy scan found no USB serials, local absolute paths, tty/by-id paths, prior approval phrase or credential patterns in `docs/hardware-evidence/public/`.
- `git diff --check` — passed after the final source and documentation edits.

No screenshot is archived or claimed. The GTKWave executable is present as version 3.3.128; the browser API served the genuine 107,364-byte blink FST. GTKWave's GUI launch was not part of this validation pass.

## Before recording

1. Start the API and Vite dev server using [`GETTING_STARTED.md`](GETTING_STARTED.md).
2. Confirm health, capabilities, device inventory and run-history in the live dashboard.
3. Open the existing Dabao run by its exact ID; do not trigger execution.
4. Open the existing blink FST in GTKWave and label it as simulation.
5. Keep Dabao and M5Stick in the camera frame if desired. The M5Stick should be described as running Bruce and not connected to the BIOScope host protocol.
6. Keep device serials, private paths and the mounted update volume out of public camera framing.

The full shot list and narration are in [`DEMO_VIDEO_GUIDE.md`](DEMO_VIDEO_GUIDE.md); exact startup and browsing steps are in [`GETTING_STARTED.md`](GETTING_STARTED.md).
