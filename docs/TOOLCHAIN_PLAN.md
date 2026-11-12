# BIO-sim Toolchain Verification

## Upstream evidence and completed baseline

Official repository: https://github.com/baochip/bio-sim (branch `main`). The GitHub README retrieved during this session describes a Verilator harness for the BIO BDMA block. It documents:

- Local simulator: `make build`, then `./simulate configs/smoke.jsonc`.
- Firmware build: from `sw/`, `python3 -m ziglang build "-Dmodule=blink"`.
- Smoke test expectation: SFR config-info read equals `0x10000408`; FST emitted at `waveform/trace.fst`.
- Blink config: `./container-run configs/blink.jsonc`; example waveform `waveform/blink.fst`.
- Makefile fetches nlohmann/json v3.11.3 single header into `sim/json.hpp` with curl if missing.
- Waveform viewing: upstream `biowave.py`, requiring custom-built GTKWave or upstream release binary; compatibility with distro GTKWave is not established.
- Container image/prebuilt model is offered, but uses Podman/Docker and is not selected for this native workflow.

Source acquired from official GitHub remote. Revision: `7e9c9615e1c900c7ddae1c4645a87078b217abc3` (`main`). Inspected README, Makefile, `configs/smoke.jsonc`, Zig build README/script, `.github/workflows/build-image.yml`, examples and waveform helper. CI only builds/pushes the container on tags; it does not pin Zig or run the local simulator. BIO C scripts were tested with Zig **0.15.2** per `sw/README.md`; the firmware build uses Python's `ziglang` module when installed that way. The smoke simulator does not need Zig.

## Tool status and approved install

| Tool | Required version | Host version | Source/status |
|---|---|---|---|
| Verilator | README says compatible local Verilator; no pinned version | 5.052 | Official Manjaro `extra`, package 5.052-1; successfully built upstream |
| Zig | BIO C scripts tested against 0.15.2 | absent | Python package install held; not required for no-firmware smoke |
| Python | README says >=3.9 for Zig build | 3.14.7 | Present |
| `ziglang` Python package | 0.15.2 | absent | `python3 -m ziglang` is explicitly documented; not required for smoke |
| GCC, Make, Perl, LZ4 | Build dependencies inferred from Makefile/tool use | present | Host packages present |
| GTKWave | Custom upstream build/release mentioned | absent | Hold; verify viewer compatibility first |

Approved install executed by user: `sudo pacman -S --needed verilator`. Metadata before install: 7.66 MiB archive, 30.90 MiB installed; dependencies already present. No other package installed by this work.

## Next exact workflow after network recovery

1. Clone official `https://github.com/baochip/bio-sim.git` into project-local `vendor/bio-sim`; record `git rev-parse HEAD`.
2. Inspect README, `Makefile`, `configs/smoke.jsonc`, `simulate`, `rtl.f`, `.github/workflows`, Zig build files and `biowave.py` at that commit.
3. Use upstream documented JSON header fetch only after confirming network; record checksum/version.
4. Run `make build`, then `./simulate configs/smoke.jsonc`; capture stdout/stderr, exit code, expected register check and FST path.
5. Verify actual Zig pin/method before blink build.

## Initial baseline evidence (historical; superseded by the update below)

- Build command: `make build` in `vendor/bio-sim`; exit 0 with non-fatal upstream RTL warnings. Required JSON header downloaded by the upstream Makefile, nlohmann/json 3.11.3; SHA-256 `9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6`.
- Run command: `./simulate configs/smoke.jsonc`; exit 0.
- Self-check: `[selftest] sfr_cfginfo @0x04 = 0x10000408 (expect 0x10000408) -> PASS`.
- Simulation time: 902496 ps, 0 BIO firmware cycles (the official smoke is a no-firmware register self-test).
- FST: `vendor/bio-sim/waveform/trace.fst`, 46,301 bytes; SHA-256 `1697052dc6e58a290ad8f078101b2c4df4c4cabce2ab813f7154735d1e8849ae`.
- BIOScope API adapter run: `SIMULATED`, exit 0, recorded in `artifacts/bio-sim-smoke.manifest.json`; copied trace at `artifacts/runs/588db51c-1f85-41e4-bf7d-b26c0bf385a3/trace.fst`.
- Blink firmware build: `.venv/bin/python -m ziglang build -Dmodule=blink -Demit-listing=false`; Zig 0.15.2, BIO errata check PASS, 40-byte BIO binary (10 words). Default listing step fails if no RISC-V objdump exists; disabling optional listing succeeds.
- Blink run: `./simulate configs/blink.jsonc`, exit 0; 10,000 cycles; `gpio_dir[21]` becomes output and `gpio_out[21]` changes repeatedly. FST size 107,364 bytes.
- GTKWave official Manjaro package metadata: `extra/gtkwave 3.3.128-1`, 2.37 MiB download / 3.98 MiB installed; package includes `fst2vcd`, `fstminer`, `gtkwave`, and example `.fst` files. This confirms FST format support. Installation has not completed because sudo authentication timed out; the user is running `sudo pacman -S --needed gtkwave`. FST artifacts and signal transitions are already exposed through the dashboard; GUI opening remains pending.
- Dabao udev confirms `/dev/ttyACM0` and by-id link. Another USB `1a86:55d4` USB-UART appeared on `/dev/ttyACM1`; board identity is unverified. Neither was opened.

## Hardware-target probe update (2026-11-12)

The table above records the earlier baseline and is superseded for current availability by this update: Zig 0.15.2 is present in project `.venv` and GTKWave 3.3.128 was later installed by the user from pacman and previously validated with FST loads. Verilator 5.052 remains installed. No dependencies were installed during this hardware investigation.

- Current BIO-sim revision: `7e9c9615e1c900c7ddae1c4645a87078b217abc3`.
- Official `bio-loader` source inspected at commit `a827a3c944c44c1b507e4eab55c76fc67871a8ca` (temporary read-only clone under `/tmp/bio-loader-inspect`; not added as a duplicate repo).
- Added `experiments/bio/dabao_fifo_probe/main.c`: `push_fifo0(0xB105C0DEu)` then `wait_quantum()` forever; no GPIO or pin setup.
- Build command: `python3 scripts/build-dabao-bio-probe.py`; exit 0. The script runs project `.venv/bin/python -m ziglang cc -S` with BIO-sim's `riscv32-freestanding`, `generic_rv32+zmmul+c`, and reserved x16–x31 flags, then the upstream `sw/clang2rustasm.py --emit-binary` pipeline. Upstream post-link errata validation: PASS; 20-byte image. Build manifest `artifacts/builds/dabao_fifo_probe/manifest.json`; image SHA-256 `cfc0502faf630bae4088e06131f23594d1b14928549743eb774d396b88e6b69b`.
- The allow-listed `dabao-fifo-probe` simulation loads that exact image, runs BIO core 0, drains FIFO0, and validates `0xb105c0de`; it also captures a genuine run FST. Evidence is `SIMULATED`, never physical. Details go in each run manifest.
- Upstream physical workflow uses `bio-loader` at 1,000,000 baud and the Xous console `bio` command. Source inspection confirms code is written to application keystore and `bio reload` starts the core. `bio rx <count> <timeout>` emits FIFO values to Xous logs. No installed Xous/app version was queried; no port was opened and no command sent.
- Physical upload can replace an existing stored BIO image. No verified backup/readback path was found. The interface's CDC open/reset behavior is unverified. Physical execution is disabled pending explicit operator approval; no GPIO experiment is prepared because board-level safe observation is unverified.
- Official Xous source sparse snapshot at `99bbfcc15320561f09a97e9ebb5e05a673ca3379` confirms `dabao-console` registers `bio` in its command table and implements documented read-only `ver xous`. It confirms BIO HAL/API service methods (`init_core`, resource claims, start state) and Dabao application keystore ranges 0–122 for stored BIO configuration and code. `cargo`, `rustc`, and `rustup` are absent on this host, so a local Xous target build was not attempted; no Rust/system dependencies were installed.
- Prepared `scripts/dabao-readonly-version.py`; exact profile check and one-command behavior are unit-tested with a fake transport. It has not been run. Running it requires operator approval to open `/dev/serial/by-id/[redacted Dabao persistent path]`; tty permissions are `root:uucp` 0660 and the active user lacks `uucp`.
