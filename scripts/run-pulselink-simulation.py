#!/usr/bin/env python3
"""Run the allow-listed PulseLink BIO program in the official BIO-sim RTL."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "vendor/bio-sim"
BUILD = ROOT / "artifacts/builds/pulselink_signal_generator"
BINARY = BUILD / "pulselink_signal_generator.bin"
SOURCE = ROOT / "experiments/bio/pulselink_signal_generator/main.c"

def run(run_dir: Path, timeout: int = 240) -> dict:
    simulator = UPSTREAM / "build/bio_sim"
    if not simulator.is_file() or not BINARY.is_file():
        raise FileNotFoundError("build official BIO-sim and the PulseLink BIO program first")
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    config = run_dir / "pulselink-simulation.json"
    trace = run_dir / "trace.fst"
    cfg = {
        # Low RTL clock keeps the 10-second virtual run tractable while retaining
        # the same 7 kHz quantum target; this is a time-accelerated simulation.
        "fclk_mhz": 0.35,
        "commands": [
            {"cmd":"monitor", "signal":"gpio_out", "bit":1},
            {"cmd":"monitor", "signal":"gpio_dir", "bit":1},
            {"cmd":"load", "core":0, "bin":os.path.relpath(BINARY, UPSTREAM)},
            {"cmd":"clock", "core":0, "style":"int", "freq_hz":7000},
            {"cmd":"start", "cores":[0], "restart":True, "clkdiv_restart":True},
            {"cmd":"run", "cycles":4200000, "stop_on_trap":False},
        ],
        "trace":{"file":os.path.relpath(trace, UPSTREAM)},
    }
    config.write_text(json.dumps(cfg, indent=2) + "\n")
    started = time.time()
    try:
        proc = subprocess.run([str(simulator), str(config)], cwd=UPSTREAM, text=True,
                              capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        (run_dir / "stdout.log").write_text(stdout)
        (run_dir / "stderr.log").write_text(stderr + f"\nSimulation timed out after {timeout}s; no successful result claimed.\n")
        raise
    elapsed = time.time() - started
    (run_dir / "stdout.log").write_text(proc.stdout)
    (run_dir / "stderr.log").write_text(proc.stderr)
    (run_dir / "configuration.json").write_text(json.dumps(cfg, indent=2) + "\n")
    gpio = [int(value) for value in re.findall(r"\[mon\].*gpio_out\[1\]: [01] -> ([01])", proc.stdout)]
    rising = sum(1 for a,b in zip([0] + gpio, gpio) if a == 0 and b == 1)
    falling = sum(1 for a,b in zip([0] + gpio, gpio) if a == 1 and b == 0)
    checks = {
        "exit_zero": proc.returncode == 0,
        "gpio_configured_output": "gpio_dir[1]: 0 -> 1" in proc.stdout,
        "ten_rising_edges": rising == 10,
        "ten_falling_edges": falling == 10,
        "safe_final_low": bool(gpio) and gpio[-1] == 0,
        "genuine_fst_generated": trace.is_file() and trace.stat().st_size > 0,
    }
    manifest = {
        "run_id":run_dir.name, "experiment_id":"pulselink_signal_generator",
        "mode":"SIMULATION", "evidence":"SIMULATED", "exit_code":proc.returncode,
        "duration_seconds":round(elapsed, 4), "source":str(SOURCE.relative_to(ROOT)),
        "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "bio_binary_sha256":hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "bio_sim_revision":subprocess.run(["git","-C",str(UPSTREAM),"rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip(),
        "tool_versions":{"verilator":subprocess.run(["verilator","--version"],capture_output=True,text=True,check=True).stdout.strip(),
                         "zig":subprocess.run([str(ROOT/".venv/bin/python"),"-m","ziglang","version"],capture_output=True,text=True,check=True).stdout.strip()},
        "configuration_path":str(config.relative_to(ROOT)),
        "configuration_sha256":hashlib.sha256(config.read_bytes()).hexdigest(),
        "signal":{"pin":"BIO1 / GPIO_PB1", "physical_header_pin":29,
                  "quantum_hz":7000,"half_period_quantums":3500,"rising_edges":rising,"falling_edges":falling,
                  "observed_gpio_out_levels":gpio,"final_level":gpio[-1] if gpio else None},
        "validation":checks,
        "artifacts":[{"path":str(trace.relative_to(ROOT)),"kind":"FST","evidence":"SIMULATED",
                       "size_bytes":trace.stat().st_size if trace.exists() else 0,
                       "sha256":hashlib.sha256(trace.read_bytes()).hexdigest() if trace.exists() else None}],
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return manifest

if __name__ == "__main__":
    dest = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else ROOT / "artifacts/runs" / ("pulselink-sim-" + str(uuid.uuid4()))
    result = run(dest)
    raise SystemExit(0 if all(result["validation"].values()) else 1)
