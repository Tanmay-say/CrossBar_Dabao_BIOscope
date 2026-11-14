# Safety and Hardware Rules

## Connections
Connect Dabao and M5StickC Plus2 independently to Manjaro with data-capable USB cables. PulseLink adds one narrowly scoped, separately approved signal path documented in `PULSELINK_WIRING.md`; no board wiring is installed or authorized yet. Do not add other wiring/modules.

## Dabao update volume
Windows previously showed a `BAOCHIP` FAT32 update volume (E:) alongside a serial interface. This is historical evidence only. On Manjaro, do not auto-mount/write, format, repair, rename, or delete files from any candidate update volume. Identify it using USB metadata and official docs. Any update procedure needs separate review and approval.

## Historical Windows USB clues (verify on Manjaro)
- Dabao serial: VID/PID `1D50:6196`, COM6; separate BAOCHIP update volume.
- M5Stick CH9102 USB-UART: VID/PID `1A86:55D4`, COM4.
Do not assume these persist or uniquely identify the device. Use lsusb, udevadm, /dev/serial/by-id and unplug/replug confirmation.

## Permissions
Inspect groups and device permissions first. Do not add `uucp`/`dialout`, change udev rules, or use sudo without approval.

## Approval required
Flashing, erase, bootloader changes, update-volume writes, state-changing serial commands, privileged installs, AUR, udev/group changes, Git push, deployment, destructive cleanup.

Before approval, state exact command, working directory, target identity, expected changes, risk and recovery.

## Current serial boundary (2026-11-12)

- Both USB identities are matched using VID/PID, unique USB serial and topology; the M5Stick association is operator-correlated and USB descriptors identify its QinHeng bridge only.
- PulseLink: Dabao BIO1/header 29 to Plus2 Grove GPIO32 through 1 kΩ, plus header 28 GND to Grove GND. Leave Grove 5 V and GPIO33 open. The nominal source/receiver voltage specifications are compatible, but measure the actual Dabao output before connecting.
- Never invoke the PulseLink serial option while Bruce is installed. Serial opening can reset the M5Stick; only enable it after a separately approved firmware replacement and acceptance of that reset behavior.
- BIO code upload, `bio pin`, `bio clk` and `bio reload` change persistent Xous keystore/configuration or start the BIO core. Each PulseLink hardware run needs separate explicit approval.
- The M5Stick persistent link is `/dev/serial/by-id/[redacted M5Stick persistent path]`; it resolves to the CH9102 USB bridge. The host bridge performs descriptor preflight but deliberately raises `PhysicalSerialDisabled` before creating a serial object.
- Linux `cdc_acm`/TTY open asserts modem lines; PySerial applies DTR/RTS after open. Since reset-free opening is not proven, Bruce `info` was not sent. No serial connection or device communication is claimed.
- Current Dabao profile: `1d50:6197`, product `Dabao`, CDC ACM interface 02, matched with serial, topology and its exact persistent link (unique values redacted in public prose). Xous `v0.10.1-43-g8964027ff` and the one completed FIFO0 operation are recorded in the physical run. Historical `1d50:6196` remains a separate bootloader-compatible observation.
- Official `bio-loader` is a state-changing interface: it persists uploaded BIO image chunks in the Xous application keystore and `bio reload` starts a BIO core. No readback/backup of an existing stored BIO image has been verified. The loader opens CDC without a reset-free line-control guarantee. Dabao CDC was opened once for the approved physical run and then closed; it was not opened during this final pass.
- The mounted BAOCHIP update volume was not queried for contents, opened, copied, changed or unmounted.

## Evidence labels
- NOT RUN: no attempt.
- BLOCKED: cannot proceed.
- COMPILE_ONLY: compiler completed.
- SIMULATED: simulator executed.
- HARDWARE EXECUTED: command ran on physical board; result not independently checked.
- HARDWARE VERIFIED: physical result captured and compared with explicit expected condition.
Never report simulated/compiled results as hardware pass.
