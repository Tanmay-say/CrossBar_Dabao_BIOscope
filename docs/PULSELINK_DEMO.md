# PulseLink two-board demo runbook

## Current status

The BIO program and Plus2 receiver firmware compile, and the host parser/dashboard implementation is prepared. The Plus2 still has Bruce; neither firmware nor BIO program has been installed for PulseLink. Physical wiring is not yet approved/connected. Use simulation until those separate approvals and electrical checks are complete.

## Safe software demonstration today

1. Start the host and dashboard using `docs/GETTING_STARTED.md`; **do not** pass `--enable-pulselink-serial` while Bruce is installed.
2. Open the PulseLink page. It should say `NO LIVE HARDWARE TELEMETRY` and show a disconnected/USB-present state. That is the truthful current state.
3. Click **Run BIO-sim baseline**. The resulting FST is explicitly simulation evidence and represents GPIO transitions from the official BIO RTL, not a signal measured across two physical boards.
4. Open the simulation run in GTKWave. Label it `SIMULATION`.
5. Show the physical Dabao FIFO0 run in Run History as recorded evidence. It is a separate physical experiment and is not PulseLink.

## Physical demonstration (authorization given; execution pending)

1. Revalidate the M5Stick USB bridge by the full profile, then run the authorized PlatformIO command in `PULSELINK.md`. Bruce will be replaced; the operator waived the backup requirement. Verify the upload, splash and telemetry before proceeding.
2. Run the authorized Dabao preparation command in `PULSELINK.md`. It persists `bio pin 1`, `bio clk 7000`, uploads the 58-byte generator and commits it with `bio pad`, overwriting the stored BIO image. It does not reload or execute the program.
4. With the M5Stick signal lead disconnected, measure Dabao pin 29 against pin 28. Confirm a safe 0–3.3 V waveform, ten rises at approximately 1 Hz, and final LOW. Stop if the measured HIGH might exceed 3.6 V.
5. After the operator confirms the wiring is connected, continue: Dabao header 29 → 1 kΩ → Plus2 Grove yellow/GPIO32; Dabao 28 GND → Grove black GND. Leave red 5 V and white GPIO33 open.
6. Power boards separately over USB. Start backend explicitly with `--enable-pulselink-serial` only after the firmware is installed and the possible reset caused by serial open is accepted.
7. Start the approved Dabao signal run. The Plus2 should show WAITING, SIGNAL DETECTED with actual rising count/frequency/level, then COMPLETE at ten rises after the input returns LOW.
8. Dashboard PulseLink should change to `LIVE HARDWARE TELEMETRY`; inspect actual events and measurements. After a complete clean capture, open the genuine edge-timestamp VCD in GTKWave. The trace is digital GPIO32 transitions at `micros()` timestamp resolution; it is not an FST or high-speed analyzer trace.
9. Save the generated run ID, manifest and VCD hash as evidence. Do not rerun unless the stored Dabao BIO content and approval are re-evaluated.

## Physical preparation commands

Build only (does not flash or touch Dabao):

```bash
./.venv/bin/python scripts/build-pulselink-bio.py
scripts/build-m5stick.sh
```

Simulation only:

```bash
./.venv/bin/python scripts/run-pulselink-simulation.py
```

After separately approved M5Stick replacement and operator confirmation, start live serial telemetry with:

```bash
./.venv/bin/python apps/host/server.py --host 127.0.0.1 --port 8765 --enable-pulselink-serial
```

This option opens only the strict M5Stick by-id profile and may reset the MCU. It does not upload firmware or operate Dabao. The Dashboard has no hardware run button; Dabao write/execution remains a separate, manually reviewed action.
