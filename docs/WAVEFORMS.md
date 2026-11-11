# FST waveform inspection

GTKWave 3.3.128 is installed from the official Manjaro repository. `gtkwave --version` reports `GTKWave Analyzer v3.3.128`; `fst2vcd` and `fstminer` are present. The package includes FST examples and its GTKWave binary loads the BIOScope run files, reporting 13,485 facilities and 5,001 signals / 8,484 aliases.

## Reproduce the traces

```sh
python3 apps/host/server.py
```

In the dashboard, run `BIO-sim smoke test`, `BIO configuration register inspection`, or `BIO GPIO blink` with `SIMULATION`. The run card offers **Open in GTKWave** and **Download FST**. The launcher only opens a manifest-indexed, verified FST under that run's artifact directory; it returns clear errors if GTKWave, the display session, or artifact is missing.

Equivalent CLI launch:

```sh
gtkwave artifacts/runs/<run-id>/trace.fst
```

The BIO-sim `biowave.py` helper is for named firmware demos with matching `.dis` files and the upstream GTKWave layout. Smoke/register tests have no BIO firmware disassembly, so direct GTKWave launch is the appropriate viewer path.

## Inspect blink GPIO 21

Convert the genuine waveform without modifying it:

```sh
fst2vcd artifacts/runs/<blink-run-id>/trace.fst > /tmp/bioscope-blink.vcd
```

In GTKWave, expand `TOP`, add `gpio_dir[31:0]` and `gpio_out[31:0]`, and inspect bit 21. In the captured run, `gpio_dir[21]` changes to output, then `gpio_out[21]` toggles repeatedly. The simulation log has matching cycle/time records. The FST timestamps are offset by 1,429 ps from the log's reported times; edge order and values match.

GTKWave viewer observation is separate from the machine-readable API signal summary and is not physical pin evidence.
