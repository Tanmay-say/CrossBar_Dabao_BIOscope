# M5StickC Plus2 firmware

The official Plus2 setup uses ESP32-PICO-V3-02 with PlatformIO `espressif32@6.7.0`, board `m5stick-c`, Arduino framework and M5Unified. The firmware provides a BIOScope screen, A/B experiment navigation, C run request and JSON protocol v1 status/results.

## Build (compile only)

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install platformio==6.2.0
scripts/build-m5stick.sh
```

The build is reproducible with the pinned M5Unified commit and ArduinoJson version in `platformio.ini`. Build output is ignored at `firmware/m5stick-plus2/.pio/`. **Do not run `pio run -t upload`** unless flashing is explicitly approved. Build verified successfully in this workspace; firmware has not been flashed or run on hardware.

The prepared host bridge is `apps/host/m5stick_bridge.py`; it expects a BIOScope protocol-v1 hello and is not started by the API automatically. **Do not run it against the connected device while Bruce is installed.** Bruce uses a separate documented command protocol; no serial connection has been made. Keep Bruce intact unless a separately reviewed replacement and recovery plan is approved. See `docs/DEVICE_DISCOVERY.md` and `docs/HARDWARE_INTEGRATION.md`.

Official source: [M5Stack StickC Plus2 documentation](https://docs.m5stack.com/en/core/StickC-Plus2).
