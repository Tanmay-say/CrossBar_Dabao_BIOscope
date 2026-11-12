# Safety and Hardware Rules

## Connections
Connect Dabao and M5StickC Plus2 independently to Manjaro with data-capable USB cables. Do not connect board pins together or add external wiring/modules.

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
- The M5Stick persistent link is `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B1E046678-if00`; it resolves to the CH9102 USB bridge. The host bridge performs descriptor preflight but deliberately raises `PhysicalSerialDisabled` before creating a serial object.
- Linux `cdc_acm`/TTY open asserts modem lines; PySerial applies DTR/RTS after open. Since reset-free opening is not proven, Bruce `info` was not sent. No serial connection or device communication is claimed.
- Dabao `/dev/ttyACM0` and its mounted update volume were not accessed.

## Evidence labels
- NOT RUN: no attempt.
- BLOCKED: cannot proceed.
- COMPILE_ONLY: compiler completed.
- SIMULATED: simulator executed.
- HARDWARE EXECUTED: command ran on physical board; result not independently checked.
- HARDWARE VERIFIED: physical result captured and compared with explicit expected condition.
Never report simulated/compiled results as hardware pass.
