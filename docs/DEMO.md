# BIOScope demo runbook

## Start

```sh
python3 apps/host/server.py
```

Open `http://127.0.0.1:8765`. The production React dashboard reads host health, experiment catalog, USB sysfs discovery and run history from the local API. Select a real upstream experiment and SIMULATION, or use MOCK for host pipeline fixtures.

## 3–5 minute walkthrough

1. Explain the goal: inspect and simulate programmable I/O on Baochip open RISC-V silicon, with honest evidence boundaries.
2. Show Host API and Verilator health, BIO-sim acquisition status, and current device detection.
3. Run BIO-sim smoke and point out the cfginfo register assertion `0x10000408`.
4. Run BIO GPIO blink and inspect the recorded GPIO 21 transitions, config hash, tool versions, upstream commit, exit code and genuine FST download.
5. Show register inspection and run history; distinguish SIMULATED evidence from MOCK and physical hardware execution.
6. Select `Dabao BIO FIFO probe (pin-free)` and run it in SIMULATION. Show the built BIO image manifest (`COMPILE_ONLY`), then the independent simulator run (`SIMULATED`), FIFO0 sentinel `0xB105C0DE`, validation checks, and genuine `trace.fst`. Explain that the same source has no GPIO operations.
7. Show the physical run `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62` in Run History. Open its result to show Dabao `[Dabao serial redacted]`, Xous version, `HARDWARE_VERIFIED`, expected and actual FIFO0 value `0xB105C0DE`, and the captured target log. Explain that the single approved operation replaced stored BIO code; no documented image backup exists. No GPIO or electrical measurement is claimed.

## Evidence boundary

The simulator adapter invokes only fixed upstream config and binary paths; no UI-supplied shell command runs. SIMULATED evidence remains distinct from the physical run. USB discovery reads sysfs, interface metadata and by-id links without opening a port; the one approved Dabao session was a separate fixed host CLI operation and closed the port. Mock artifacts are never presented as waveforms. Bruce's `info` command was not sent. The Dabao update volume remains untouched. Further physical writes require separate approval because the upload overwrites the stored BIO image and no backup/readback procedure exists.

## Waveform segment

Use **Open in GTKWave** on the blink run. Expand `TOP`, add `gpio_dir[31:0]` and `gpio_out[31:0]`, then inspect bit 21. Compare repeated edges with the GPIO transition lines in the run's stdout. See `docs/WAVEFORMS.md` for the exact FST conversion and the documented 1,429 ps trace-origin offset.
