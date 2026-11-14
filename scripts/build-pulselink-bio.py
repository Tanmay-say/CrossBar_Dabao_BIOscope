#!/usr/bin/env python3
"""Compile the allow-listed PulseLink signal generator with pinned BIO-sim tools."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "vendor/bio-sim"
SOURCE = ROOT / "experiments/bio/pulselink_signal_generator/main.c"
OUT = ROOT / "artifacts/builds/pulselink_signal_generator"
SW = UPSTREAM / "sw"
PYTHON = ROOT / ".venv/bin/python"

if not PYTHON.is_file() or not (UPSTREAM / "sw/build.zig").is_file():
    raise SystemExit("Project .venv and pinned official BIO-sim source are required")
OUT.mkdir(parents=True, exist_ok=True)
zig_dir = OUT / "zig-out"
zig_dir.mkdir(exist_ok=True)
binary = OUT / "pulselink_signal_generator.bin"
assembly = zig_dir / "pulselink_signal_generator.s"
rust = OUT / "pulselink_signal_generator.rs"
module_path = subprocess.run(
    [str(PYTHON), "-c", "import pathlib, ziglang; print(pathlib.Path(ziglang.__file__).with_name('zig'))"],
    capture_output=True, text=True, check=True,
).stdout.strip()
zig_exe = Path(module_path)
if not zig_exe.is_file():
    raise SystemExit("ziglang package did not provide its Zig executable")

env = os.environ.copy()
env["ZIG_GLOBAL_CACHE_DIR"] = str(ROOT / ".cache/zig-global")
register_flags = [f"-ffixed-x{register}" for register in range(16, 32)]
mcpu = "generic_rv32+zmmul+c+" + "+".join(f"reserve_x{r}" for r in range(16, 32))
compile_cmd = [str(PYTHON), "-m", "ziglang", "cc", "-S", "-fno-jump-tables", "-fverbose-asm",
               "-o", str(assembly), str(SOURCE), "-target", "riscv32-freestanding", "-mcpu=" + mcpu,
               f"-I{SOURCE.parent}", f"-I{SW / 'include'}", "-std=c11", "-Wall", "-Wextra",
               "-ffreestanding", "-fno-common", "-ffunction-sections", "-fdata-sections", "-Os", *register_flags]
print("$", " ".join(compile_cmd), flush=True)
subprocess.run(compile_cmd, cwd=ROOT, env=env, check=True)
translate_cmd = [str(PYTHON), str(SW / "clang2rustasm.py"), "pulselink_signal_generator",
                 "--zig-out", str(zig_dir), "-o", str(rust), "--emit-binary", "--zig-exe", str(zig_exe)]
print("$", " ".join(translate_cmd), flush=True)
subprocess.run(translate_cmd, cwd=ROOT, env=env, check=True)
if not binary.is_file() or binary.stat().st_size == 0:
    raise SystemExit("BIO translator emitted no binary")

manifest = {
    "experiment_id": "pulselink_signal_generator",
    "classification": "COMPILE_ONLY",
    "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "upstream_repository": "https://github.com/baochip/bio-sim",
    "bio_sim_revision": subprocess.run(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(),
    "zig_version": subprocess.run([str(PYTHON), "-m", "ziglang", "version"], capture_output=True, text=True, check=True, env=env).stdout.strip(),
    "target": "BIO RV32IMC; official clang2rustasm translator with errata/link validation",
    "pin": {"bio_pin": 1, "dabao_gpio": "PB1", "header_physical_pin": 29, "direction": "output"},
    "timing": {"requested_quantum_hz": 7000, "half_period_quantums": 3500,
               "expected_period_seconds": 1.0, "rising_edges": 10, "safe_final_level": 0,
               "timing_note": "Integer divider from 350 MHz is 50000; compiler loop overhead is small but physical rate requires instrumented validation."},
    "persistent_xous_setup": ["bio pin 1", "bio clk 7000", "upload 64-byte indexed Base64 chunks", "bio pad", "bio reload"],
    "binary": str(binary.relative_to(ROOT)),
    "binary_size_bytes": binary.stat().st_size,
    "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
    "errata_validation": "PASS if official translator completes (required for manifest generation)",
    "physical_execution": "NOT RUN; persistent BIO keystore write requires separate approval",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
