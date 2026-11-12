# Hardware integration status

## Exact-version FIFO0 probe preflight (2026-11-12)

The operator reports a successful physical version response: `Xous version: v0.10.1-43-g8964027ff`. Its exact source revision, `8964027fff25f8b85d3d3c63933d365ac7614523`, was fetched and inspected at `apps-dabao/dabao-console/src/cmds/bio.rs`. This revision supports `bio ready`, a base64 70-byte BIO chunk (`u16` big-endian index + 64-byte payload + `u32` big-endian CRC32 over the preceding 66 bytes), `bio pad`, `bio reload`, and `bio rx <count> <timeout-seconds>`. `bio pad` zero-fills all missing chunks in the 0xF00-byte image and commits it to the Xous application keystore. `bio reload` loads and starts the core. `bio rx 1 5` reads one FIFO0 word and logs it; the Xous implementation logs `timeout` but still reads the FIFO register afterward, so the host uses one request only and requires the actual logged sentinel before validating.

The 20-byte binary matches its compile manifest and SHA-256; the C source emits `0xB105C0DE` to FIFO0 and calls no pin/GPIO configuration. The protocol implementation and fake-serial tests are in `apps/host/dabao_adapter.py` and `apps/host/test_dabao_fifo_probe.py`; `scripts/run-dabao-fifo-probe.py` now exits locked without device discovery because the one-shot operation is complete. The operator ran it once after explicit approval on 2026-11-12. Run `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62` captured the physical FIFO0 response and is recorded `HARDWARE_VERIFIED`. No retry occurred.

No documented readback command exists for a stored BIO image, so any existing valid image cannot be backed up through this console. Xous startup loads an image when its validity marker is set; a previous program may be running now. The probe's `bio pad` commit replaces the existing stored code with a full 0xF00-byte image (20 source bytes plus 44 zeros in chunk 0 and 59 zero chunks). `bio reload` reinitializes the core. It does not send `bio pin` or `bio clk`, but reload reapplies the board's existing pin configuration; that state has no readback in this command interface. The experiment contains no GPIO instructions and needs no wiring. See the exact [pinned Xous implementation](https://github.com/betrusted-io/xous-core/blob/8964027fff25f8b85d3d3c63933d365ac7614523/apps-dabao/dabao-console/src/cmds/bio.rs).

The preceding was the approval request for the operation that has now completed. It used Dabao serial `[Dabao serial redacted]`, persistent link `/dev/serial/by-id/[redacted Dabao persistent path]`, 1,000,000 baud 8N1 with DTR/RTS requested low, and only the documented commands listed. The result and logs are below and in the run directory. The stored BIO program was replaced; no recovery image is available. No firmware was flashed and the BAOCHIP update volume was not accessed. The API/dashboard expose this completed record read-only; API hardware writes are disabled, and the fixed CLI refuses another attempt after any recorded attempt.

## Current physical BIO path investigation (2026-11-12)

The operator-reported live USB profile at the time of the run was Dabao `1d50:6197`, serial `[Dabao serial redacted]`, topology `1-4`, product `Dabao`, CDC ACM interface 2 and persistent link `[redacted Dabao persistent path]`. The approved host process opened and closed the CDC port for the one physical probe; background discovery remains read-only.

Current upstream BIO-sim documentation points physical loading to Baochip's `bio-loader` and the Xous `dabao-console` BIO command. The inspected bio-loader revision is `a827a3c944c44c1b507e4eab55c76fc67871a8ca`. It opens CDC ACM at 1,000,000 baud, uploads 64-byte chunks, sends `bio pad` to zero-fill the rest of the 0xF00-byte code area when needed, and invokes `bio reload`. The Xous implementation writes chunks and a validity marker into application keystore entries; `reload` initializes the BIO core and sets it running. The documented `bio rx <count> <timeout-seconds>` command reads the RX FIFO and writes values to the Xous log. Sources: [BIO-sim](https://github.com/baochip/bio-sim), [bio-loader source](https://github.com/baochip/bio-loader/blob/main/bio-loader/bio_loader.py), [Xous BIO console source](https://github.com/betrusted-io/xous-core/blob/dev/apps-dabao/dabao-console/src/cmds/bio.rs), [Xous Baochip build and boot notes](https://github.com/betrusted-io/xous-core/blob/dev/README-baochip.md).

This path is confirmed against the operator-reported Xous version and exact source revision above. The loader operation was state-changing: it replaced the stored BIO program and started the BIO core. No verified readback/backup method for the previous image exists. Opening USB CDC may reset the board even when DTR/RTS are requested low; this behavior was not independently characterized.

The Xous API exposes `BioApi::init_core`, core run-state methods, resource claiming, FIFO handles, and register access through the `bao1x-api`/`bao1x-hal` layers. `dabao-console` registers its BIO loader command at startup. BIO C is compiled by the official BIO-sim Zig 0.15.2 + `clang2rustasm.py --emit-binary` pipeline; the resulting flat BIO binary is what `bio-loader` sends. The official Xous app build target is `cargo xtask dabao dabao-console`; the Xous guide locates UF2 outputs under the RISC-V Xous target release directory. This host has no `cargo`/`rustc`, so no Xous app binary was built. Sources: [BIO API](https://github.com/betrusted-io/xous-core/blob/dev/libs/bao1x-api/src/bio.rs), [Dabao app build guide](https://github.com/betrusted-io/xous-core/blob/dev/README-baochip.md).

The official boot guide describes holding `PROG` while connecting USB to enter the update mass-storage bootloader; it requires copying UF2s and pressing `PROG` to apply them. Initial firmware replacement requires aligned `loader.uf2`, `xous.uf2`, and `apps.uf2`; subsequent app-only updates may use `apps.uf2` when loader/kernel versions are compatible. Baochip's security notes warn that introducing an untrusted/developer boot-chain image can erase on-chip secrets. No recovery/update action is attempted or proposed here because BIO transfer through the currently documented console is the less invasive path if already supported. If it is absent, firmware update requires a separate exact-operation approval, signed-image review and backup/recovery assessment. We do not use or write the mounted update volume.

### Prepared pin-free probe

`experiments/bio/dabao_fifo_probe/main.c` emits the constant `0xB105C0DE` once on FIFO0, then waits. It contains no GPIO operations. Build with:

```sh
python3 scripts/build-dabao-bio-probe.py
```

The build invokes the pinned BIO-sim Zig 0.15.2 compiler target flags and upstream `clang2rustasm.py --emit-binary` converter/post-link errata scan. The built binary is 20 bytes and evidence is `COMPILE_ONLY`; see `artifacts/builds/dabao_fifo_probe/manifest.json`. BIOScope also ran this image through BIO-sim using a fixed in-project config and received the FIFO0 sentinel with a genuine FST; that result is **SIMULATED**, not physical evidence. Run the host simulation from Experiment Explorer as `Dabao BIO FIFO probe (pin-free)`.

### Physical run approval boundary

The operator provided the successful read-only Xous version output, then separately approved and ran the fixed physical probe. `/api/hardware/capabilities` reports the verified run. The run history endpoint returns its captured logs and physical manifest; dashboard/API execution cannot initiate another hardware write.

The one approved physical operation completed: `bio ready`; upload of chunk 0; `bio pad`; `bio reload`; `bio rx 1 5`; port close. It returned `b105c0de`, exactly matching expected `0xB105C0DE`. `HARDWARE_VERIFIED` means the documented target console logged the expected FIFO0 word and the host captured it. This does not prove GPIO pad behavior or external electrical activity. Further writes need separate approval.

No official physical pad was selected for GPIO activity. Simulation GPIO 21 is not treated as a Dabao board pin. Board-level GPIO experiment remains unsupported without an official mapping and an allowed safe observation path.

## Dabao (read-only discovery)

The previous hardware report recorded `1d50:6196` with interface 00. Current descriptors instead identify `1d50:6197`, product `Dabao`, serial `[Dabao serial redacted]`, topology `1-4`, CDC ACM interface 02, by-id `[redacted Dabao persistent path]`. Neither observation has been silently substituted for the other. The current interface set did not include mass storage, and the mounted BAOCHIP filesystem remains untouched.

Official Xous docs describe the USB serial console, `cargo xtask dabao dabao-console` build, and boot1 update channel. The operator-reported Xous version and the exact BIO console source revision are recorded above and in the run manifest. Physical PB13/PB14 serial is documented as 1,000,000 baud 8N1; do not infer USB CDC behavior from that physical UART specification. Source: [Xous Baochip README](https://github.com/betrusted-io/xous-core/blob/dev/README-baochip.md), [Xous console docs](https://github.com/betrusted-io/xous-core/blob/dev/README-consoles.md), [boot-chain documentation](https://github.com/betrusted-io/xous-core/blob/dev/bao1x-boot/BOOTCHAIN.md).

## M5StickC Plus2 preparation

Official board docs identify ESP32-PICO-V3-02 and a supported PlatformIO/Arduino setup (`espressif32@6.7.0`, board `m5stick-c`, M5Unified). The BIOScope firmware project in `firmware/m5stick-plus2` compiles locally but has **not** been flashed. Bruce remains installed. Host-side bounded framing/parser and request handler in `apps/host/serial_protocol.py` and `apps/host/m5stick.py` are tested as software components; they do not currently communicate with this Bruce device. Source: [M5Stack Plus2 documentation](https://docs.m5stack.com/en/core/StickC-Plus2).

Read-only event correlation associated the operator-connected M5Stick with the CH9102 USB UART: `1a86:55d4`, serial `[M5Stick bridge serial redacted]`, topology `1-3`, CDC ACM and by-id name `[redacted M5Stick persistent path]`. These descriptors identify the USB bridge only. Dabao is independently matched by VID/PID + observed product + serial + topology + exact persistent link; serial link status is separate from USB presence.

Bruce's official [Serial wiki](https://github.com/BruceDevices/firmware/wiki/Serial) documents a 115200 8N1 command interface with diagnostics (`info`, `uptime`, `free`) and state-changing operations (IR/RF transmit, GPIO, storage writes/deletes, power controls, factory reset). The BIOScope JSONL hello protocol is not the Bruce protocol; there is no safe generic command-forwarding adapter. No port was opened; DTR/RTS were not toggled. The integration decision is to preserve Bruce, defer command access, and require explicit approval before any serial session. See [device discovery and safe integration](DEVICE_DISCOVERY.md).

Xous documents USB serial boot1 console access and `cargo xtask dabao dabao-console`; boot1 also accepts commands and update files. The Dabao CDC console was opened only for the approved Xous BIO probe, then closed. The BAOCHIP update volume remains untouched. Dabao firmware upload, bootloader changes and storage-volume access remain prohibited without separate explicit approval.
