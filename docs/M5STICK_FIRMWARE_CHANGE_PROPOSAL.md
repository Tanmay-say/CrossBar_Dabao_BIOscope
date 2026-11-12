# M5Stick firmware preservation and replacement proposal

## Decision

Keep the currently installed Bruce firmware. Its official serial interface documents diagnostics (`info`, `uptime`, `free`) and a much broader command surface that can transmit IR/RF, change GPIO, access storage and control power. It does not implement BIOScope's JSONL experiment protocol. A restricted Bruce diagnostics adapter may be possible, but it would not provide the BIOScope operator UI or execute the BIO-sim experiment catalog. No command or port has been used to identify the installed Bruce version.

## Candidate path: retain Bruce

The documented single read-only request is `info` at 115200 8N1. That diagnostic was not attempted: inspection of the host serial stack and Linux `cdc_acm`/TTY open path shows DTR/RTS assertion during open, followed by PySerial line-state ioctls. ModemManager is also active and the interface is a candidate for probing. A reset-free open cannot be guaranteed, so the port remains unopened and Bruce's state is unchanged. The bridge now fails closed before constructing a serial transport. Generic command forwarding remains disallowed.

This path would provide Bruce device diagnostics only. It would not make the device send BIOScope experiment requests or display BIOScope run results through its current firmware. Bruce's documented WebUI and BLE command facilities also expose command execution/file controls and are not treated as a restricted BIOScope API.

## Candidate path: install BIOScope firmware (not approved or performed)

1. Identify the installed Bruce version using the approved read-only process, if available.
2. Locate an official Bruce Plus2 release matching that version and record its published checksum. Investigate whether a full flash readback can be obtained without altering boot state; do not assume it is possible. An ESP32 bootloader/readback operation may require reset/download-mode control and therefore needs separate explicit authorization.
3. Record the existing Bruce configuration and storage preservation limits. No guarantee is made that settings or files can be restored from an application firmware image alone.
4. Review the BIOScope PlatformIO image, its source commit and checksum, and the exact target path. The current compile-only `.bin` is 525,856 bytes and has never been uploaded.
5. Review a recovery path before any upload. M5Stack's official [Plus2 factory restore guide](https://docs.m5stack.com/en/guide/stickc_plus2/restore_factory) uses M5Burner to install factory firmware. This restores M5Stack factory firmware; it is **not** a backup of the user's Bruce image or Bruce data. The official [Bruce firmware repository/releases](https://github.com/BruceDevices/firmware/releases) is a possible source for a matching Bruce image, but the exact installed version and release image are not known.
6. Present all artifacts, hashes, data-loss limits, upload command/tool and recovery steps for separate approval. Do not flash until explicitly authorized.

## Safety boundary

Bruce firmware remains preserved. No serial port open, DTR/RTS change, reset, readback, flash, erase or device storage operation has been performed. The BIOScope firmware build and protocol tests are compile/mock evidence only; they do not establish compatibility on the physical M5Stick. Official Bruce supports its own serial diagnostics and WebUI, but does not document the BIOScope JSON protocol or catalog run/result exchange. Bruce may be retained for its native diagnostics only if a future connection method is shown to avoid unsafe line transitions; it cannot currently provide the BIOScope operator workflow.
