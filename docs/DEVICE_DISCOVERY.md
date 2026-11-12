# BIOScope device discovery and safe integration status

## Identity profiles

BIOScope independently tracks Dabao and the M5Stick-associated CH9102 bridge. A profile matches only when **VID, PID, USB serial and USB topology** all match. It also requires the profile's exact `/dev/serial/by-id` link before publishing a usable persistent serial path. VID/PID alone never identifies a board.

| Profile | VID:PID | USB serial | Topology | by-id link | Confidence |
|---|---|---|---|---|---|
| Baochip-1x Dabao (current) | `1d50:6197` | `[Dabao serial redacted]` | `1-4` | `[redacted Dabao persistent path]` | High descriptor match: product + VID/PID + serial + topology + exact by-id link; firmware/app stage unverified |
| Baochip-1x Dabao (historical observation) | `1d50:6196` | `[Dabao serial redacted]` | `1-4` | `[redacted Dabao persistent path]` | Historical profile only; not the current enumeration |
| M5StickC Plus2 association | `1a86:55d4` | `[M5Stick bridge serial redacted]` | `1-3` | `[redacted M5Stick persistent path]` | High association: operator-reported M5Stick connection plus matching bridge arrival; the USB descriptors prove only the QinHeng serial bridge |

Discovery reads `/sys/bus/usb/devices`, interface driver links and `/dev/serial/by-id`. It never opens a tty. USB presence and serial-link availability are independent fields. The dashboard polls `/api/devices` every two seconds; its live process history reports connection transitions and last verification/change times. These timestamps are in-memory and restart with the host. No udev rule or permission change is installed.

## M5Stick / Bruce

The official [Bruce Serial wiki](https://github.com/BruceDevices/firmware/wiki/Serial) documents USB serial at 115200 baud, 8 data bits, no parity, one stop bit, and a broad command interface. It lists diagnostics such as `info`, `uptime`, and `free`, but also state-changing commands including radio transmit, GPIO control, storage write/delete, reboot/sleep and factory reset. Its [official WebUI docs](https://github.com/BruceDevices/Wiki/blob/main/docs/controlling-device/webui.md) document file management, command execution and reboot controls. This interface is not BIOScope's JSON protocol.

BIOScope therefore does not run `m5stick_bridge.py` against the currently installed Bruce firmware. That bridge expects a BIOScope firmware `hello` frame, which Bruce does not document. Linux's [`cdc_acm` driver](https://github.com/torvalds/linux/blob/master/drivers/usb/class/cdc-acm.c) and [TTY port open path](https://github.com/torvalds/linux/blob/master/drivers/tty/tty_port.c) assert DTR/RTS when opening an active tty; [PySerial's POSIX backend](https://github.com/pyserial/pyserial/blob/master/serial/serialposix.py) also applies its configured DTR/RTS states after opening. The observed M5Stick bridge is a CDC ACM candidate and ModemManager is active. A reset-free open therefore cannot be guaranteed. In accordance with the safety condition, the port was not opened and the documented `info` request was not sent. Bruce remains untouched. The preserve-Bruce and future replacement/recovery assessment is in [M5Stick firmware change proposal](M5STICK_FIRMWARE_CHANGE_PROPOSAL.md).

**Integration decision:** keep Bruce installed for this milestone. A future Bruce diagnostics adapter would require an operator-approved session and a strict allow-list of independently verified read-only commands; generic command forwarding is prohibited. Bruce cannot provide the full BIOScope M5Stick experiment-selection/result UI using the current firmware protocol. A replacement proposal identifies its recovery limits and M5Stack factory restore path; no firmware replacement or backup operation has been performed.

## Dabao / Xous

Official [Xous Baochip documentation](https://github.com/betrusted-io/xous-core/blob/dev/README-baochip.md) documents USB serial console access and `cargo xtask dabao dabao-console` as a build target. The [boot-chain documentation](https://github.com/betrusted-io/xous-core/blob/dev/bao1x-boot/BOOTCHAIN.md) states that boot1's console accepts update files and serial commands. The current device exposes `1d50:6197`, product `Dabao`, CDC ACM interface 02. The operator reported Xous `v0.10.1-43-g8964027ff`; the one completed BIO FIFO0 transaction confirms the console responded on that run. The mounted BAOCHIP volume remains untouched.

Current BIO-sim documentation names Baochip's official [bio-loader](https://github.com/baochip/bio-loader). The loader's documented protocol is implemented by upstream `dabao-console/src/cmds/bio.rs`: it receives base64-encoded 64-byte BIO chunks with CRC, stores them in Xous keystore, and `bio reload` initializes/starts a BIO core. `bio rx <count> <timeout>` reads FIFO output. The direct source reviewed is [bio.rs](https://github.com/betrusted-io/xous-core/blob/dev/apps-dabao/dabao-console/src/cmds/bio.rs); bio-loader revision `a827a3c944c44c1b507e4eab55c76fc67871a8ca`. This documented transport is state-changing; no loader command has been sent. Details and the pin-free probe are in [hardware integration](HARDWARE_INTEGRATION.md).

The Xous source inspected at `99bbfcc15320561f09a97e9ebb5e05a673ca3379` registers the BIO command in `dabao-console`. Its documented `ver xous` command is read-only. `scripts/dabao-readonly-version.py` is a one-shot exact-device query with no user-supplied command parameter; it has not been run because opening USB CDC may reset the board and the current user's `uucp` permissions are absent.

## Safe future serial session requirements

Before any physical serial session, verify (a) the stable USB identity and topology again, (b) the active firmware/protocol from an official source, (c) line-control behavior without toggling DTR/RTS or resetting, (d) a strictly read-only command set, and (e) operator approval. Device commands must be adapter-owned and allow-listed. The dashboard and M5Stick must never supply arbitrary shell or serial commands.

## Current integration truth

- Functional now: identity-profile matching, persistent by-id correlation, interface/driver inventory, independent Dabao/M5Stick status, disconnect/reconnect reflected by polling, and dashboard Hardware Devices view.
- No general-purpose physical serial protocol is implemented. The one fixed Dabao FIFO0 probe completed in the recorded run; the one-shot path is now consumed. Bruce command execution remains unsupported, and firmware update/flash is not part of BIOScope.
- During the current read-only discovery check, both ports remained unopened and DTR/RTS were unchanged. Historically, the approved Dabao probe opened its exact CDC port once and closed it. The M5Stick `info` response was not obtained: opening it could reset the device, so Bruce remains untouched.
