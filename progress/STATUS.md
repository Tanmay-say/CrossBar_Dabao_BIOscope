# BIOScope Status

**Updated:** 2026-11-12
**Current milestone:** Three official BIO-sim experiments, genuine FST artifacts, GTKWave launch, React dashboard and read-only hardware profile discovery are integrated. Both USB serial ports remain unopened.

## Verified working

- Official BIO-sim source at `7e9c9615e1c900c7ddae1c4645a87078b217abc3`; smoke, register inspection (`sfr_cfginfo == 0x10000408`) and blink pass in simulation.
- Blink simulation emits genuine FST; GPIO 21 transitions were correlated with logs and loaded in GTKWave.
- Host API and React/TypeScript/Vite dashboard expose experiment runs, logs, manifests, validation and artifacts.
- M5Stick Plus2 BIOScope firmware compiles with the documented PlatformIO target (compile-only; it was not flashed).
- New USB profile matcher uses VID/PID + USB serial + USB topology and exact `/dev/serial/by-id` link. The dashboard has a separate Hardware Devices page and polls device inventory every 2 seconds.
- New tests cover exact-profile match, VID/PID-only rejection, topology mismatch, USB presence with inaccessible serial link, and disconnect/reconnect transitions. Device API timestamps describe current-process history and reset after host restart.
- Bruce serial workflow researched from official documentation. The documented `info` command at 115200 8N1 was not sent: Linux CDC ACM/TTY opening asserts DTR/RTS, PySerial applies line states after open, and ModemManager is active. Reset-free opening cannot be guaranteed, so the fail-closed bridge never constructs a serial object.
- Full M5Stick integration assessment and a preserve-Bruce/recovery proposal are documented in `docs/M5STICK_FIRMWARE_CHANGE_PROPOSAL.md`.
- Xous USB console/build documentation reviewed. Boot1 serial console can accept commands and update files; active stage is unverified, so console remains unopened.

## Current host visibility

Previously verified host inventory identifies Dabao `1d50:6196`, serial `TLZ4A6`, topology `1-4`, and M5Stick-associated bridge `1a86:55d4`, serial `5B1E046678`, topology `1-3`, with persistent by-id names. M5Stick identity is operator-correlated; descriptor evidence alone identifies its QinHeng bridge, not the M5Stack board model. Current dashboard reports USB identity and tty link availability as separate states. This task did not open either port.

## Safety state

- Bruce firmware remains installed and untouched. No flash, erase, reset or serial command was performed.
- `/dev/ttyACM0` and the M5Stick by-id port were not opened by BIOScope; BIOScope changed no DTR/RTS state.
- The mounted BAOCHIP volume remains untouched. No Dabao console session or firmware write occurred.
- No M5Stick protocol session exists: Bruce does not implement BIOScope JSON hello. The local BIOScope bridge is not to be run against Bruce.

## Latest validation

- Backend: all 33 tests passed, including device profile/reconnect tests, strict protocol validation, fail-closed physical opener, mock transport framing/timeouts, API integration and the built-in BIO-sim smoke/blink tests.
- Frontend: `npm run build` passed (TypeScript `tsc -b` and Vite production build; 29 modules bundled).
- Python compilation and `git diff --check` passed.
- Existing genuine manifests verify smoke and register inspection at exit 0 with `cfginfo_pass`; blink exit 0 with `gpio21_transitions`, 65 `gpio_out[21]` edges and its verified 107,364-byte FST. GTKWave/FST inspection was previously verified and is documented in `docs/WAVEFORMS.md`.
- No screenshot is archived: headless Firefox attempts returned API-offline/blank captures, which were discarded instead of being presented as evidence.
- Hardware integration tests use temporary sysfs/by-id fixtures; they do not access hardware serial devices.

See [device discovery and safe integration](../docs/DEVICE_DISCOVERY.md), [hardware integration](../docs/HARDWARE_INTEGRATION.md), [architecture](../docs/ARCHITECTURE.md), and [demo runbook](../docs/DEMO.md).
