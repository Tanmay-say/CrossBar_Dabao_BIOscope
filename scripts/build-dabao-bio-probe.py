#!/usr/bin/env python3
"""Build BIOScope's pin-free FIFO probe with the official BIO-sim toolchain."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "vendor/bio-sim"
SW = UPSTREAM / "sw"
SOURCE = ROOT / "experiments/bio/dabao_fifo_probe/main.c"
OUT = ROOT / "artifacts/builds/dabao_fifo_probe"
MODULE = "dabao_fifo_probe"
PYTHON = ROOT / ".venv/bin/python"

if not PYTHON.is_file():
    raise SystemExit("Project .venv with upstream-tested Zig 0.15.2 is required")
if not SOURCE.is_file() or not (SW / "build.zig").is_file():
    raise SystemExit("Probe source or pinned upstream BIO-sim build source is missing")

OUT.mkdir(parents=True, exist_ok=True)
assembly = OUT / f"{MODULE}.s"
zig = OUT / "zig-out"  # upstream converter consumes an assembly file from this folder
zig.mkdir(parents=True, exist_ok=True)
assembly = zig / f"{MODULE}.s"
binary = OUT / f"{MODULE}.bin"
rust = OUT / f"{MODULE}.rs"
module_path = subprocess.run(
    [str(PYTHON), "-c", "import pathlib, ziglang; print(pathlib.Path(ziglang.__file__).with_name('zig'))"],
    capture_output=True, text=True, check=True,
).stdout.strip()
zig_exe = Path(module_path)
if not zig_exe.is_file():
    raise SystemExit("The Zig executable from the active ziglang Python package was not found")

env = os.environ.copy()
env["ZIG_GLOBAL_CACHE_DIR"] = str(ROOT / ".cache/zig-global")
zig_cmd = [str(PYTHON), "-m", "ziglang", "cc", "-S", "-fno-jump-tables", "-fverbose-asm",
           "-o", str(assembly), str(SOURCE), "-target", "riscv32-freestanding",
           "-mcpu=generic_rv32+zmmul+c" + "+reserve_x16+reserve_x17+reserve_x18+reserve_x19"
           "+reserve_x20+reserve_x21+reserve_x22+reserve_x23+reserve_x24+reserve_x25"
           "+reserve_x26+reserve_x27+reserve_x28+reserve_x29+reserve_x30+reserve_x31",
           f"-I{SOURCE.parent}", f"-I{SW / 'include'}", "-std=c11", "-Wall", "-Wextra",
           "-ffreestanding", "-fno-common", "-ffunction-sections", "-fdata-sections", "-Os"]
zig_cmd.extend(f"-ffixed-x{register}" for register in range(16, 32))
print("$", " ".join(zig_cmd), flush=True)
subprocess.run(zig_cmd, cwd=ROOT, env=env, check=True)

convert_cmd = [str(PYTHON), str(SW / "clang2rustasm.py"), MODULE, "--zig-out", str(zig),
               "-o", str(rust), "--emit-binary", "--zig-exe", str(zig_exe)]
print("$", " ".join(convert_cmd), flush=True)
subprocess.run(convert_cmd, cwd=ROOT, env=env, check=True)

upstream_rev = subprocess.run(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
zig_version = subprocess.run([str(PYTHON), "-m", "ziglang", "version"],
                             capture_output=True, text=True, env=env, check=True).stdout.strip()
if not binary.is_file() or binary.stat().st_size == 0:
    raise SystemExit("Upstream BIO translator did not produce a non-empty binary")
manifest = {
    "experiment_id": "dabao-fifo-probe", "evidence": "COMPILE_ONLY",
    "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "bio_sim_revision": upstream_rev, "zig_version": zig_version,
    "build_command": "python -m ziglang cc -S <BIO-sim RV32IMC/reserved-register flags>; upstream clang2rustasm.py --emit-binary",
    "target": "riscv32-freestanding; BIO-sim official C-to-Rust-asm translator and errata/link check",
    "program_effect": "Push one 0xB105C0DE word to BIO FIFO0, then wait_quantum forever; no GPIO/pads touched.",
    "binary": str(binary.relative_to(ROOT)), "binary_size_bytes": binary.stat().st_size,
    "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
    "errata_validation": "PASS (upstream converter post-link scan)",
    "hardware_execution": "NOT RUN",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
