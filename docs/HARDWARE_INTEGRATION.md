# Hardware integration status

## Dabao (read-only discovery)

udev identifies `/dev/ttyACM0` as `Baochip-1x`, USB `1d50:6196`, serial `TLZ4A6`; `/dev/serial/by-id/usb-Baochip_Baochip-1x_TLZ4A6-if00` resolves to that node. Kernel interfaces include CDC ACM and USB mass storage. No console bytes were read and no serial command was sent. The mounted `BAOCHIP` filesystem remains untouched.

Official Xous Baochip documentation describes the USB serial console and `cargo xtask dabao dabao-console` build. It also describes USB mass storage as the bootloader update channel for UF2s. The CDC ACM node is visible as `/dev/ttyACM0`; no bytes were read, so console readiness/protocol state is not verified. Physical PB13/PB14 serial is documented as 1,000,000 baud 8N1; do not apply that baud assumption to USB CDC ACM. BIOScope will only build firmware offline and will gate any hardware transfer behind explicit approval. Source: [Xous Baochip README](https://github.com/betrusted-io/xous-core/blob/dev/README-baochip.md), [Dabao app README](https://github.com/betrusted-io/xous-core/blob/dev/apps-dabao/README.md).

## M5StickC Plus2 preparation

Official board docs identify ESP32-PICO-V3-02 and a supported PlatformIO/Arduino setup (`espressif32@6.7.0`, board `m5stick-c`, M5Unified). The firmware project is in `firmware/m5stick-plus2`; it implements display/button states and newline-delimited JSON protocol v1 framing in source, but has not yet been built or flashed. Host-side bounded framing/parser and request handler are in `apps/host/serial_protocol.py` and `apps/host/m5stick.py`; they are unit tested, but no serial transport is opened. Source: [M5Stack Plus2 documentation](https://docs.m5stack.com/en/core/StickC-Plus2).

When physical connection is requested: connect only the M5StickC Plus2 to a Manjaro USB data port using a data-capable USB-C cable; expected inventory is a CH9102 USB UART (`1a86:55d4`) and a new `/dev/ttyACM*`/serial-by-id entry. Do not connect pins to Dabao. Firmware upload must be separately approved.
