# M5StickC Plus2 BIOScope firmware

This project builds the BIOScope PulseLink receiver for the Plus2: GPIO32 input, rising-edge count/frequency estimate, low-speed transition timestamps, screen status, Button A measurement reset, Button B page change, and protocol-v1 newline-delimited JSON telemetry.

## Compile only

```sh
scripts/build-m5stick.sh
```

Verified target: PlatformIO Espressif32 6.7.0, `m5stick-c`, Arduino 2.0.16, M5Unified commit `96576a14247ddc935149145aa6b51943464120f1`, ArduinoJson 7.4.3. The binary compiled successfully in this workspace. Build output is ignored at `firmware/m5stick-plus2/.pio/`.

**The firmware has not been flashed. Bruce remains installed.** Do not run `pio run -t upload` or `esptool write_flash` without separate explicit approval. A complete Bruce backup has not been produced or verified. Read `docs/PULSELINK.md` before proposing replacement or recovery.

The host telemetry reader is opt-in and USB serial open may reset the M5Stick. Do not use `--enable-pulselink-serial` while Bruce is installed. The receiver sends measurements only; it does not accept commands to run hardware or arbitrary host operations.

Official board reference: [M5Stack M5StickC Plus2 documentation](https://docs.m5stack.com/en/core/StickC-Plus2).
