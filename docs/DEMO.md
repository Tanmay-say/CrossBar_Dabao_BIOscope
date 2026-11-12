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

## Evidence boundary

The simulator adapter invokes only fixed upstream config and binary paths; no UI-supplied shell command runs. SIMULATED evidence is not physical board execution. USB discovery reads sysfs, interface metadata and by-id links; it opens no serial port. Mock artifact files are never presented as waveforms. Bruce's documented `info` command was not sent because Linux CDC ACM opening asserts DTR/RTS and reset-free opening cannot be guaranteed. The Dabao console/update-volume path remains untouched.

## Waveform segment

Use **Open in GTKWave** on the blink run. Expand `TOP`, add `gpio_dir[31:0]` and `gpio_out[31:0]`, then inspect bit 21. Compare repeated edges with the GPIO transition lines in the run's stdout. See `docs/WAVEFORMS.md` for the exact FST conversion and the documented 1,429 ps trace-origin offset.
