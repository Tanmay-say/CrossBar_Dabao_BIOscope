# Physical hardware evidence index

## Dabao FIFO0 sentinel

- Run ID: `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`
- Classification: `HARDWARE_VERIFIED`
- Target: Baochip-1x Dabao, USB VID/PID `1d50:6197`; unique serial, topology, persistent device path, and Linux node are withheld from public evidence.
- Xous version: `v0.10.1-43-g8964027ff`; exact source revision `8964027fff25f8b85d3d3c63933d365ac7614523`.
- Expected and captured FIFO0: `0xB105C0DE`.
- Probe source SHA-256: `f4d25b67b5f7481cc1447cfb8b346c458500022583e7d74b4c66c7fbbc119ac2`.
- Compiled BIO image: 20 bytes; SHA-256 `cfc0502faf630bae4088e06131f23594d1b14928549743eb774d396b88e6b69b`.

Public, sanitized copies of the manifest, hardware result, stdout/stderr, amendment and checksum index are in [`public/`](public/). The local raw run directory is git-ignored and has not been modified. The public copy redacts the USB serial, topology, by-id path, Linux tty path, approval phrase and echoed Base64 payload. Checksums are recomputed for each published file in `public/integrity.json`.

The initial manifest's operation description said 63 zero chunks. The pinned Xous implementation uses 60 chunks in 0xF00 bytes total, so the correct count after uploaded chunk 0 is 59. The public copy contains the corrected description; its amendment records the raw manifest checksum and redactions. This does not change the command result.

No genuine dashboard screenshot is archived. Headless capture attempts were blank or lacked API-backed content and were discarded. The verified evidence is the captured Xous FIFO0 response and run artifacts, not a screenshot.
