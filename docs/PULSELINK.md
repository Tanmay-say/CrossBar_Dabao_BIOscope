# BIOScope PulseLink

PulseLink is the first planned two-board signal experiment: Dabao BIO drives a low-rate digital output, the M5StickC Plus2 samples edges on GPIO32, and the host receives measured telemetry. The physical flow is **prepared and compiled, not yet executed**.

## Current implementation status

- **Dabao BIO program:** compiled from `experiments/bio/pulselink_signal_generator/main.c` with the official BIO-sim compiler/translator at BIO-sim revision `7e9c9615e1c900c7ddae1c4645a87078b217abc3`; 58-byte image, errata/link check passed. Build classification: `COMPILE_ONLY`.
- **M5Stick firmware:** Plus2 PlatformIO build succeeds with Espressif32 6.7.0, Arduino 2.0.16, M5Unified pinned commit `96576a14247ddc935149145aa6b51943464120f1`, ArduinoJson 7.4.3. Firmware is not flashed; Bruce remains installed.
- **Host:** strict protocol-v1 JSON telemetry parser, optional by-id serial monitor, live status API and actual edge-derived VCD writer are implemented. Discovery never opens the serial port. Real telemetry has not been received.
- **Dashboard:** PulseLink view distinguishes `SIMULATION`, `LIVE HARDWARE`, and no telemetry. It displays no waveform until actual GPIO32 edge events arrive. Start/stop hardware controls are intentionally absent.
- **GTKWave:** simulation output is FST; a completed physical capture is VCD built only from M5Stick interrupt timestamps. GTKWave can inspect the completed VCD. This is a low-rate digital edge record, not an analog or high-resolution logic-analyzer capture. The VCD is not currently a continuously refreshed live GTKWave session.

## BIO program and timing

The program sets the BIO output mask to bit 1, sets it as output, establishes LOW, then repeats ten HIGH/LOW periods. Each half period waits 3,500 BIO quanta. The Xous 0.10.1 console implementation at commit `8964027fff25f8b85d3d3c63933d365ac7614523` defaults the BIO core to 350 MHz and accepts integer target frequency through the `bio clk` setting. `bio clk 7000` gives integer divider 50,000 and a nominal 7 kHz quantum; 3,500 quanta are 0.5 seconds. The program returns to LOW after the tenth falling edge and then waits forever.

The Xous loader configures the physical pin mux from the persistent pin selection, separately from the C program. The exact future console preparation is `bio pin 1`, then `bio clk 7000`, then upload, pad and reload. These operations persist configuration and BIO code in the Xous application keystore. Uploading the program replaces the currently stored BIO image. **Do not run these operations without a separate approval.**

The built image and checksums are in `artifacts/builds/pulselink_signal_generator/manifest.json` on this machine. Rebuild with:

```bash
./.venv/bin/python scripts/build-pulselink-bio.py
```

The safe simulation command is:

```bash
./.venv/bin/python scripts/run-pulselink-simulation.py
```

The simulator uses a time-accelerated RTL clock and preserves the target 7 kHz quantum setting; its manifest and FST are evidence classified `SIMULATED`, never physical. The API catalog can run the same simulation with experiment id `pulselink_signal_generator` and mode `SIMULATION`.

The authorized Plus2 upload command, to run from the repository root after revalidating the M5Stick profile, is:

```bash
sudo env PLATFORMIO_CORE_DIR="$PWD/.cache/platformio" "$PWD/.venv/bin/pio" run \
  --project-dir "$PWD/firmware/m5stick-plus2" -e m5stack-stickc-plus2 -t upload \
  --upload-port /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B1E046678-if00
```

PlatformIO writes its bootloader, partition table and application image; this command does not request a whole-chip erase. The agent attempted it after confirming the exact USB profile, but `sudo` stopped for lack of an interactive password TTY before PlatformIO ran or the device was opened. Run the command in an interactive terminal and provide its complete output so boot and telemetry can be verified.

After M5Stick boot/telemetry verification, stage the authorized Dabao program/configuration with:

```bash
sudo .venv/bin/python scripts/prepare-pulselink-dabao.py \
  --approval STAGE_PULSELINK_BIO1_7000HZ_NO_RELOAD_TLZ4A6
```

The helper revalidates the exact Dabao identity and image hash; sends `bio pin 1`, `bio clk 7000`, one indexed 64-byte Base64/CRC32 chunk and `bio pad`; saves a preparation manifest and logs; then closes the port. It deliberately does not send `bio reload`, so the newly committed program is not started before the operator confirms the wiring.

## Plus2 receiver and host

GPIO32 is configured input with pulldown. An interrupt records both signal transitions using `micros()`, counts only rising edges, and estimates frequency from consecutive rising-edge timestamps. USB serial emits bounded newline-delimited protocol-v1 JSON at 10 Hz. Button A clears the measurement; Button B changes the display page. The receiver does not accept host commands and cannot start a Dabao operation.

Once BIOScope firmware has been separately approved and installed, the host's explicitly opt-in serial mode is:

```bash
./.venv/bin/python apps/host/server.py --host 127.0.0.1 --port 8765 --enable-pulselink-serial
```

Opening the USB serial port may reset the M5Stick. Do not use this option while Bruce is installed. `/api/pulselink` returns the latest verified profile/telemetry state. Stale telemetry becomes disconnected after two seconds. A completed capture produces a manifest and `pulselink.vcd` only after ten observed rising edges, ten observed falling edges, an initial/final LOW, ordered timestamps and no receiver queue overflow.

## Physical demo prerequisites

1. Review [`PULSELINK_WIRING.md`](PULSELINK_WIRING.md), including its voltage check.
2. The operator has authorized replacing Bruce and overwriting the stored Dabao BIO image; no Bruce backup has been produced or verified, and the operator has waived that requirement for this experiment.
3. Revalidate the Plus2 USB profile before flashing, then capture PlatformIO output and confirm the device's BIOScope splash and JSON telemetry. The attempted upload stopped at the sudo prompt and has not yet run.
4. Measure the Dabao output HIGH/LOW with a meter before connecting it to GPIO32. Keep Grove 5 V disconnected.
5. Start the host with the explicit serial option only after firmware installation and reset behavior are accepted.
6. Wait until the operator confirms that the physical wire and ground are connected. Only then reload/start the staged BIO program, start the host's serial bridge and run the single physical experiment.

The M5Stick telemetry provides measured pulse count, frequency estimate, current input level and edge times. Only the edge times are used to export a VCD; no FST is synthesized from telemetry.

## References

- [Pinned Xous Dabao BIO console implementation](https://github.com/betrusted-io/xous-core/blob/8964027fff25f8b85d3d3c63933d365ac7614523/apps-dabao/dabao-console/src/cmds/bio.rs)
- [Pinned Xous BIO HAL](https://github.com/betrusted-io/xous-core/blob/8964027fff25f8b85d3d3c63933d365ac7614523/libs/bao1x-hal/src/bio_hw.rs)
- [Dabao official pinout](https://github.com/baochip/dabao/tree/main/docs/pinout)
- [Dabao evaluation board schematic source](https://github.com/baochip/dabao/blob/main/dabao_v3c.kicad_sch)
- [M5StickC Plus2 official pin map](https://docs.m5stack.com/en/core/StickC-Plus2)
- [Espressif GPIO electrical limits](https://docs.espressif.com/projects/esp-faq/en/latest/esp-faq-en-master.pdf)
