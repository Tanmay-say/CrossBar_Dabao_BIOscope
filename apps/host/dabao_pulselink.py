"""Authorized PulseLink BIO image staging for the pinned Xous console.

This operation persists BIO1 selection, the 7 kHz quantum rate and the new BIO
image. It intentionally does not send ``bio reload`` or execute the program.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading
import time
import uuid
import zlib

from device_discovery import discover

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/bio/pulselink_signal_generator/main.c"
BUILD = ROOT / "artifacts/builds/pulselink_signal_generator"
BINARY = BUILD / "pulselink_signal_generator.bin"
BUILD_MANIFEST = BUILD / "manifest.json"
RUNS = ROOT / "artifacts/runs"
XOUS_COMMIT = "8964027fff25f8b85d3d3c63933d365ac7614523"
TARGET = {"vid":"1d50", "pid":"6197", "product":"Dabao", "serial":"TLZ4A6", "topology":"1-4",
          "port":"/dev/serial/by-id/usb-Baochip_Dabao_TLZ4A6-if02"}
BAUD = 1_000_000
IMAGE_CAPACITY = 0xF00
CHUNK_SIZE = 64
_LOCK = threading.Lock()


class PulseLinkPrepareError(RuntimeError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_chunk(image: bytes) -> bytes:
    if not image or len(image) > CHUNK_SIZE:
        raise ValueError("PulseLink image must fit in one 64-byte BIO chunk")
    payload = b"\x00\x00" + image.ljust(CHUNK_SIZE, b"\x00")
    return payload + (zlib.crc32(payload) & 0xFFFFFFFF).to_bytes(4, "big")


def verify_target(discovery=discover) -> dict:
    candidates = discovery()
    target = next((item for item in candidates if item.get("id") == "dabao"), None)
    expected = (TARGET["vid"], TARGET["pid"], TARGET["product"], TARGET["serial"], TARGET["topology"], TARGET["port"])
    actual = None if target is None else (target.get("vid"), target.get("pid"), target.get("observed_product"),
                                          target.get("serial"), target.get("usb_topology"), target.get("persistent_port"))
    if not target or not target.get("connected") or not target.get("serial_link_available") or actual != expected:
        raise RuntimeError(f"Dabao identity/path mismatch; expected {expected}, observed {actual}")
    if target.get("serial_opened") is not False:
        raise RuntimeError("Dabao CDC ownership state is not safe")
    return target


def verify_build() -> tuple[bytes, dict]:
    if not (SOURCE.is_file() and BINARY.is_file() and BUILD_MANIFEST.is_file()):
        raise FileNotFoundError("PulseLink BIO source, binary or build manifest is missing")
    manifest = json.loads(BUILD_MANIFEST.read_text())
    image = BINARY.read_bytes()
    if (manifest.get("experiment_id") != "pulselink_signal_generator" or
            manifest.get("classification") != "COMPILE_ONLY" or len(image) != 58 or
            manifest.get("binary_size_bytes") != len(image) or manifest.get("binary_sha256") != sha256(image) or
            manifest.get("source_sha256") != sha256(SOURCE.read_bytes()) or
            manifest.get("pin", {}).get("bio_pin") != 1 or
            manifest.get("timing", {}).get("requested_quantum_hz") != 7000):
        raise ValueError("PulseLink build manifest/hash/target configuration mismatch")
    return image, manifest


def _read_until(conn, expected: str, timeout: float, lines: list[str]) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        raw = conn.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip() if isinstance(raw, bytes) else str(raw).strip()
        if not line:
            continue
        lines.append(line)
        response = line.removeprefix("[console]").strip()
        if response == expected:
            return response
        if response == "ERR" or response.startswith("ERR ") or response.startswith("Write failure:"):
            raise PulseLinkPrepareError(f"Dabao returned {response}")
    raise TimeoutError(f"timeout waiting for documented response {expected!r}")


def _exchange(conn, command: str, expected: str, timeout: float, lines: list[str]) -> None:
    if "\r" in command or "\n" in command:
        raise ValueError("console command must be one line")
    conn.write(command.encode("ascii") + b"\n")
    _read_until(conn, expected, timeout, lines)


def _drain_startup(conn, lines: list[str]) -> None:
    deadline = time.monotonic() + 0.8
    while time.monotonic() < deadline:
        raw = conn.readline()
        if raw:
            item = raw.decode("utf-8", errors="replace").strip() if isinstance(raw, bytes) else str(raw).strip()
            if item:
                lines.append(item)
            deadline = time.monotonic() + 0.15


def stage_pulselink(*, serial_module=None, discovery=discover, run_root: Path = RUNS) -> dict:
    """Set BIO1/7kHz and commit the program, but never reload or execute it.

    A timeout after the commit command is considered ambiguous. Do not retry;
    inspect the saved manifest and console output first.
    """
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError("another BIOScope operation owns the Dabao profile")
    run_id = "pulselink-stage-" + str(uuid.uuid4())
    run_dir = Path(run_root) / run_id
    lines: list[str] = []
    phase = "preflight"
    commit_attempted = False
    committed = False
    target = None
    failure = None
    conn = None
    started = time.time()
    try:
        target = verify_target(discovery)
        image, build = verify_build()
        chunk = make_chunk(image)
        encoded = base64.b64encode(chunk).decode("ascii")
        if serial_module is None:
            import serial as serial_module
        conn = serial_module.Serial(port=None, baudrate=BAUD,
                                   bytesize=serial_module.EIGHTBITS, parity=serial_module.PARITY_NONE,
                                   stopbits=serial_module.STOPBITS_ONE, timeout=0.2,
                                   write_timeout=1.0, exclusive=True)
        conn.dtr = False
        conn.rts = False
        conn.port = TARGET["port"]
        conn.open()
        _drain_startup(conn, lines)
        # Exact pinned Xous 8964027 command handlers: both return OK and write
        # settings to the application keystore. No `ready` is sent because it
        # invalidates code and resets clock config; no `reload` is sent because
        # it starts the just-committed program before wiring is confirmed.
        phase = "configure-pin-bio1"
        _exchange(conn, "bio pin 1", "OK", 4.0, lines)
        phase = "configure-quantum-clock-7000-hz"
        _exchange(conn, "bio clk 7000", "OK", 4.0, lines)
        phase = "stage-index-zero-64-byte-chunk"
        _exchange(conn, f"bio {encoded}", "OK", 5.0, lines)
        phase = "commit-zero-padded-image-to-keystore"
        commit_attempted = True
        _exchange(conn, "bio pad", "SUCCESS", 8.0, lines)
        committed = True
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        if conn is not None:
            try:
                conn.close()
                lines.append("[host] Dabao CDC port closed")
            except Exception as exc:
                failure = (failure + "\n" if failure else "") + f"close error: {type(exc).__name__}: {exc}"
        _LOCK.release()

    manifest = {
        "run_id":run_id, "experiment_id":"pulselink_signal_generator", "mode":"HARDWARE_PREPARATION",
        "state":"PROGRAM_STAGED_NOT_RELOADED" if committed else "FAILED_OR_AMBIGUOUS",
        "evidence":"TARGET_PROGRAM_STAGED" if committed else "NOT_VERIFIED",
        "started_at":started, "finished_at":time.time(), "duration_seconds":round(time.time()-started, 4),
        "exit_code":0 if committed else 1, "hardware_profile":{k:target.get(k) for k in ("vid","pid","serial","usb_topology","persistent_port")} if target else None,
        "xous_version":"v0.10.1-43-g8964027ff", "xous_source_revision":XOUS_COMMIT,
        "source":str(SOURCE.relative_to(ROOT)), "source_sha256":sha256(SOURCE.read_bytes()),
        "binary":str(BINARY.relative_to(ROOT)), "binary_size_bytes":BINARY.stat().st_size,
        "binary_sha256":sha256(BINARY.read_bytes()), "build_manifest":str(BUILD_MANIFEST.relative_to(ROOT)),
        "bio_sim_revision":build.get("bio_sim_revision") if 'build' in locals() else None,
        "operations":["bio pin 1", "bio clk 7000", "bio <Base64(index-0 || 64-byte payload || big-endian CRC32)>", "bio pad"],
        "commit_attempted":commit_attempted, "commit_response_verified":committed,
        "reload_sent":False, "execution_started_by_this_run":False,
        "captured_responses":lines, "phase_at_failure":phase if failure else None, "failure":failure,
        "known_limitations":["No physical signal was measured.", "No GPIO wire was connected.",
                             "The program was not reloaded or executed; run it only after the operator confirms safe wiring."],
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "stdout.log").write_text("\n".join(lines) + ("\n" if lines else ""))
    (run_dir / "stderr.log").write_text((failure + "\n") if failure else "")
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if failure:
        raise PulseLinkPrepareError(f"Dabao staging stopped in {phase}; do not retry until reviewing {run_dir / 'manifest.json'}: {failure}")
    return manifest
