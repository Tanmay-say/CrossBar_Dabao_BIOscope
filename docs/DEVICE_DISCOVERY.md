# BIOScope device discovery and safe integration status

## Identity profiles

BIOScope independently tracks Dabao and the M5Stick-associated CH9102 bridge. A profile matches only when **VID, PID, USB serial and USB topology** all match. It also requires the profile's exact `/dev/serial/by-id` link before publishing a usable persistent serial path. VID/PID alone never identifies a board.

| Profile | VID:PID | USB serial | Topology | by-id link | Confidence |
|---|---|---|---|---|---|
| Baochip-1x Dabao | `1d50:6196` | `TLZ4A6` | `1-4` | `usb-Baochip_Baochip-1x_TLZ4A6-if00` | High: matching board descriptors, unique serial and observed topology |
| M5StickC Plus2 association | `1a86:55d4` | `5B1E046678` | `1-3` | `usb-1a86_USB_Single_Serial_5B1E046678-if00` | High association: operator-reported M5Stick connection plus matching bridge arrival; the USB descriptors prove only the QinHeng serial bridge |

Discovery reads `/sys/bus/usb/devices`, interface driver links and `/dev/serial/by-id`. It never opens a tty. USB presence and serial-link availability are independent fields. The dashboard polls `/api/devices` every two seconds; its live process history reports connection transitions and last verification/change times. These timestamps are in-memory and restart with the host. No udev rule or permission change is installed.

## M5Stick / Bruce

The official [Bruce Serial wiki](https://github.com/BruceDevices/firmware/wiki/Serial) documents USB serial at 115200 baud, 8 data bits, no parity, one stop bit, and a broad command interface. It lists diagnostics such as `info`, `uptime`, and `free`, but also state-changing commands including radio transmit, GPIO control, storage write/delete, reboot/sleep and factory reset. Its [official WebUI docs](https://github.com/BruceDevices/Wiki/blob/main/docs/controlling-device/webui.md) document file management, command execution and reboot controls. This interface is not BIOScope's JSON protocol.

BIOScope therefore does not run `m5stick_bridge.py` against the currently installed Bruce firmware. That bridge expects a BIOScope firmware `hello` frame, which Bruce does not document. Linux's [`cdc_acm` driver](https://github.com/torvalds/linux/blob/master/drivers/usb/class/cdc-acm.c) and [TTY port open path](https://github.com/torvalds/linux/blob/master/drivers/tty/tty_port.c) assert DTR/RTS when opening an active tty; [PySerial's POSIX backend](https://github.com/pyserial/pyserial/blob/master/serial/serialposix.py) also applies its configured DTR/RTS states after opening. The observed M5Stick bridge is a CDC ACM candidate and ModemManager is active. A reset-free open therefore cannot be guaranteed. In accordance with the safety condition, the port was not opened and the documented `info` request was not sent. Bruce remains untouched. The preserve-Bruce and future replacement/recovery assessment is in [M5Stick firmware change proposal](M5STICK_FIRMWARE_CHANGE_PROPOSAL.md).

**Integration decision:** keep Bruce installed for this milestone. A future Bruce diagnostics adapter would require an operator-approved session and a strict allow-list of independently verified read-only commands; generic command forwarding is prohibited. Bruce cannot provide the full BIOScope M5Stick experiment-selection/result UI using the current firmware protocol. A replacement proposal identifies its recovery limits and M5Stack factory restore path; no firmware replacement or backup operation has been performed.

## Dabao / Xous

Official [Xous Baochip documentation](https://github.com/betrusted-io/xous-core/blob/dev/README-baochip.md) documents USB serial console access and `cargo xtask dabao dabao-console` as a build target. The [boot-chain documentation](https://github.com/betrusted-io/xous-core/blob/dev/bao1x-boot/BOOTCHAIN.md) states that boot1's console accepts update files and serial commands. The active stage and console command state on this board have not been verified; BIOScope does not open `/dev/ttyACM0` or send input. The mounted `/run/media/tanmaymanjaro/BAOCHIP` volume remains untouched.

## Safe future serial session requirements

Before any physical serial session, verify (a) the stable USB identity and topology again, (b) the active firmware/protocol from an official source, (c) line-control behavior without toggling DTR/RTS or resetting, (d) a strictly read-only command set, and (e) operator approval. Device commands must be adapter-owned and allow-listed. The dashboard and M5Stick must never supply arbitrary shell or serial commands.

## Current integration truth

- Functional now: identity-profile matching, persistent by-id correlation, interface/driver inventory, independent Dabao/M5Stick status, disconnect/reconnect reflected by polling, and dashboard Hardware Devices view.
- Not implemented: physical serial communication, Bruce command execution, Dabao console interaction, BIO execution on silicon, firmware update or flash.
- Serial opens: **none**. DTR/RTS changes: **none**. Board writes: **none**. `info` response: **not obtained; intentionally stopped before open because reset-free open is unverified and kernel behavior asserts DTR/RTS**.
