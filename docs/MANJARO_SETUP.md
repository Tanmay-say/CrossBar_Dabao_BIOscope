# Manjaro Setup — Discovery First

No installation should happen during initial discovery. Manjaro is the primary native host; no Docker or WSL is required.

## Discovery
Run `bash scripts/discover-manjaro.sh`. Also inspect:
```bash
cat /etc/os-release
uname -a
lscpu
free -h
df -hT
rustc --version
cargo --version
python --version
gcc --version
clang --version
zig version
verilator --version
make --version
perl --version
lz4 --version
node --version
npm --version
git --version
```
Missing commands are normal; do not install automatically.

## BIO-sim verification
Read current upstream README, scripts, examples and CI:
https://github.com/baochip/bio-sim

Verify Linux support and exact Zig, Verilator, C compiler, Python, Make, Perl, LZ4, waveform tool requirements, exact baseline command and outputs. Record upstream commit. Do not rely on stale dependency lists.

## Package policy
Check official Manjaro/Arch repositories first (`pacman -Ss`, `pacman -Si`). Before installing, report package names, source (official/AUR/upstream), versions, download and installed size, and system changes. Ask approval. Review AUR PKGBUILDs; never run opaque scripts.

## Xous
Read current Baochip Xous README and bootchain docs. Verify target, Rust toolchain, build commands and recovery path. Build-only first; no flashing.

## M5Stick
Use exact Plus2 documentation: https://docs.m5stack.com/en/core/StickC-Plus2. Verify model revision, framework, display/buttons, USB transport and flashing process. Build minimal app first; ask before flashing.

## Disk discipline
Inspect free space before downloads/builds. Keep build artifacts under ignored project-local folders. Avoid duplicate clones/toolchains. Do not clear global caches without reporting size and asking.
