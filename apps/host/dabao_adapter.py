"""One-shot adapter implementation for the physical Dabao FIFO probe.

Protocol constants and command semantics are pinned to Xous commit
8964027fff25f8b85d3d3c63933d365ac7614523. Importing this module is inert; the
only serial opener is run_fifo_probe(), which revalidates the exact USB profile
and refuses any attempt after local or published hardware evidence exists.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
import re
import threading
import time
import uuid
import zlib
from pathlib import Path

from device_discovery import discover
from dabao_hardware import HardwareRun, HardwareState

ROOT = Path(__file__).resolve().parents[2]
BUILD_MANIFEST = ROOT / "artifacts/builds/dabao_fifo_probe/manifest.json"
BIO_BINARY = ROOT / "artifacts/builds/dabao_fifo_probe/dabao_fifo_probe.bin"
BIO_SOURCE = ROOT / "experiments/bio/dabao_fifo_probe/main.c"
RUNS = ROOT / "artifacts/runs"
PUBLIC_EVIDENCE_MANIFEST = ROOT / "docs/hardware-evidence/public/manifest.json"
XOUS_REVISION = "8964027fff25f8b85d3d3c63933d365ac7614523"
XOUS_VERSION = "v0.10.1-43-g8964027ff"
TARGET = {
    "profile_id": "dabao", "vid": "1d50", "pid": "6197", "product": "Dabao",
    "serial": "TLZ4A6", "topology": "1-4",
    "persistent_port": "/dev/serial/by-id/usb-Baochip_Dabao_TLZ4A6-if02",
}
# The one approved operation has already run. Keep the reviewed protocol usable
# only in isolated tests; the CLI and normal calls are permanently consumed by
# the committed public evidence record and local attempt manifest.
APPROVAL_PHRASE = "DISABLED_AFTER_VERIFIED_RUN"
EXPECTED_WORD = 0xB105C0DE
MAX_CODE_BYTES = 0xF00
CHUNK_BYTES = 64
CHUNK_WIRE_BYTES = 70
BAUD = 1_000_000
_DEVICE_LOCK = threading.Lock()
_LINE_RE = re.compile(rb"(?:\r?\n)")
_WORD_RE = re.compile(r"(?i)(?<![0-9a-f])(?:0x)?([0-9a-f]{8})(?![0-9a-f])")


class DabaoRunError(RuntimeError):
    """A physical run failed or was incomplete; inspect its saved manifest."""


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_binary():
    if not (BIO_SOURCE.is_file() and BIO_BINARY.is_file() and BUILD_MANIFEST.is_file()):
        raise FileNotFoundError("the reviewed Dabao FIFO probe build/source/manifest is missing")
    build = json.loads(BUILD_MANIFEST.read_text())
    if build.get("experiment_id") != "dabao-fifo-probe" or build.get("evidence") != "COMPILE_ONLY":
        raise ValueError("unexpected BIO probe build manifest")
    if build.get("binary_size_bytes") != 20 or BIO_BINARY.stat().st_size != 20:
        raise ValueError("probe binary size does not match the reviewed 20-byte image")
    if _sha256(BIO_BINARY) != build.get("binary_sha256"):
        raise ValueError("probe binary SHA-256 does not match its build manifest")
    if _sha256(BIO_SOURCE) != build.get("source_sha256"):
        raise ValueError("probe source SHA-256 does not match its build manifest")
    if "PASS" not in build.get("errata_validation", ""):
        raise ValueError("upstream BIO errata validation is not recorded as passing")
    return build, BIO_BINARY.read_bytes()


def make_chunk(index: int, code: bytes) -> bytes:
    """Encode one exact Xous BIO-loader chunk: index || 64 bytes || CRC32."""
    if index != 0:
        raise ValueError("this catalog experiment only uploads BIO chunk 0")
    if len(code) > CHUNK_BYTES:
        raise ValueError("the reviewed probe must fit in the first 64-byte BIO chunk")
    padded = code.ljust(CHUNK_BYTES, b"\x00")
    index_bytes = index.to_bytes(2, "big")
    payload = index_bytes + padded
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    wire = payload + checksum.to_bytes(4, "big")
    if len(wire) != CHUNK_WIRE_BYTES:
        raise AssertionError("internal BIO chunk framing error")
    return wire


def _verified_target(discovery_fn=discover):
    devices = discovery_fn()
    device = next((item for item in devices if item.get("id") == "dabao"), None)
    if not device:
        raise RuntimeError("Dabao profile is not present")
    if not (device.get("connected") and device.get("vid") == TARGET["vid"] and
            device.get("pid") == TARGET["pid"] and device.get("observed_product") == TARGET["product"] and
            device.get("serial") == TARGET["serial"] and device.get("usb_topology") == TARGET["topology"]):
        raise RuntimeError("live Dabao USB identity does not match VID/PID/product/serial/topology")
    persistent = device.get("persistent_port")
    if persistent != TARGET["persistent_port"] or not device.get("serial_link_available"):
        raise RuntimeError("exact verified Dabao persistent serial path is unavailable")
    if device.get("serial_opened") is not False:
        raise RuntimeError("Dabao port ownership/status is not safe for a new operation")
    return device


def _has_prior_attempt(runs_dir: Path) -> bool:
    """Make this probe one-shot across local runs and fresh public checkouts."""
    try:
        prior = json.loads(PUBLIC_EVIDENCE_MANIFEST.read_text())
    except (OSError, ValueError):
        prior = {}
    if prior.get("experiment_id") == "dabao-fifo-probe" and prior.get("mode") == "HARDWARE":
        return True
    root = Path(runs_dir)
    for manifest_path in root.glob("*/manifest.json"):
        try:
            prior = json.loads(manifest_path.read_text())
        except (OSError, ValueError):
            continue
        if prior.get("experiment_id") == "dabao-fifo-probe" and prior.get("mode") == "HARDWARE":
            return True
    return False


def _decode_line(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").strip()


def _read_until(connection, expected: set[str], timeout: float, log_lines: list[str], monotonic=time.monotonic):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        raw = connection.readline()
        if not raw:
            continue
        line = _decode_line(raw)
        if line:
            log_lines.append(line)
        normalized = line.removeprefix("[console]").strip()
        if normalized in expected:
            return normalized
        if normalized == "ERR" or normalized.startswith("ERR "):
            raise DabaoRunError(f"Dabao returned error: {normalized}")
    raise TimeoutError(f"timed out waiting for one of: {sorted(expected)}")


def _drain_startup(connection, log_lines: list[str], monotonic=time.monotonic):
    """Bounded read-only drain of CDC lines already queued before the handshake."""
    deadline = monotonic() + 1.0
    silent_until = monotonic() + 0.2
    while monotonic() < deadline and monotonic() < silent_until:
        raw = connection.readline()
        if raw:
            line = _decode_line(raw)
            if line:
                log_lines.append(line)
            silent_until = monotonic() + 0.2


def _exchange(connection, command: str, expected: set[str], timeout: float, log_lines: list[str], monotonic=time.monotonic):
    if "\n" in command or "\r" in command:
        raise ValueError("console command must be one bounded line")
    connection.write(command.encode("ascii") + b"\n")
    return _read_until(connection, expected, timeout, log_lines, monotonic)


def _capture_fifo_word(connection, log_lines: list[str], timeout: float = 7.0, monotonic=time.monotonic):
    """Issue exactly one `bio rx 1 5`, then parse only its captured console logs."""
    connection.write(b"bio rx 1 5\n")
    deadline = monotonic() + timeout
    got_ok = False
    captured = []
    while monotonic() < deadline:
        raw = connection.readline()
        if not raw:
            continue
        line = _decode_line(raw)
        if not line:
            continue
        log_lines.append(line)
        normalized = line.removeprefix("[console]").strip()
        if normalized == "ERR" or normalized.startswith("ERR "):
            raise DabaoRunError(f"Dabao rejected FIFO receive: {normalized}")
        if normalized == "OK":
            got_ok = True
        for match in _WORD_RE.finditer(line):
            captured.append(int(match.group(1), 16))
        if got_ok and any(value == EXPECTED_WORD for value in captured):
            return captured
    if not got_ok:
        raise TimeoutError("bio rx did not return its documented OK response within the host timeout")
    raise TimeoutError("bio rx returned but did not log the expected FIFO0 word within the host timeout")


def run_fifo_probe(approval: str, *, serial_module=None, discovery_fn=discover,
                   runs_dir: Path = RUNS, monotonic=time.monotonic):
    """Internal single-probe implementation; public runner is permanently locked.

    No other BIO image, pad, clock, shell command, or target is accepted. The
    published evidence consumes this gate; unit tests use fake serial only.
    """
    if approval != APPROVAL_PHRASE:
        raise PermissionError("physical upload blocked: explicit stored-BIO overwrite approval is required")
    if _has_prior_attempt(Path(runs_dir)):
        raise PermissionError("this physical probe already has a recorded hardware attempt; refusing to retry")
    if not _DEVICE_LOCK.acquire(blocking=False):
        raise RuntimeError("another BIOScope operation already owns the Dabao profile")
    run_id = str(uuid.uuid4())
    run_dir = Path(runs_dir) / run_id
    log_lines: list[str] = []
    stderr = ""
    connection = None
    xous_write_committed = False
    xous_commit_attempted = False
    core_reload_succeeded = False
    started_epoch = time.time()
    started_at = _utc()
    state = HardwareState.CAPABILITY_CHECK
    captured_words = []
    build = {}
    device = None
    image = b""
    chunk = b""
    phase = "preflight"
    failure = None

    try:
        device = _verified_target(discovery_fn)
        build, image = _verify_binary()
        if len(image) > MAX_CODE_BYTES:
            raise ValueError("BIO binary exceeds the Xous BIO memory limit")
        chunk = make_chunk(0, image)
        phase = "open-exclusive-dabao-cdc"
        if serial_module is None:
            import serial as serial_module
        # Match upstream bio-loader's 1 Mbaud, 8N1, but request low modem lines
        # before open and use the kernel's exclusive-open flag.
        connection = serial_module.Serial(port=None, baudrate=BAUD,
                                          bytesize=serial_module.EIGHTBITS,
                                          parity=serial_module.PARITY_NONE,
                                          stopbits=serial_module.STOPBITS_ONE,
                                          timeout=0.2, write_timeout=1.0,
                                          exclusive=True)
        connection.dtr = False
        connection.rts = False
        connection.port = TARGET["persistent_port"]
        connection.open()
        _drain_startup(connection, log_lines, monotonic)

        state = HardwareState.VALIDATING
        phase = "bio-ready"
        _exchange(connection, "bio ready", {"OK"}, 4.0, log_lines, monotonic)

        state = HardwareState.BUILDING
        encoded = base64.b64encode(chunk).decode("ascii")
        phase = "upload-chunk-0"  # staging only; commit is the next command
        _exchange(connection, f"bio {encoded}", {"OK"}, 4.0, log_lines, monotonic)

        phase = "commit-padded-bio-image"
        xous_commit_attempted = True
        _exchange(connection, "bio pad", {"SUCCESS"}, 5.0, log_lines, monotonic)
        xous_write_committed = True
        state = HardwareState.EXECUTING

        phase = "reload-start-bio-core"
        _exchange(connection, "bio reload", {"BIO load successful"}, 8.0, log_lines, monotonic)
        core_reload_succeeded = True
        phase = "read-one-fifo0-word"
        captured_words = _capture_fifo_word(connection, log_lines, 7.0, monotonic)
        captured_word = next((word for word in captured_words if word == EXPECTED_WORD), None)
        if captured_word is None:
            raise DabaoRunError("physical FIFO0 value did not match the expected probe word")
        state = HardwareState.RESULT_CAPTURED
        hardware_run = HardwareRun("dabao-fifo-probe", state=HardwareState.RESULT_CAPTURED,
                                   evidence="HARDWARE_EXECUTED", expected_observation=f"0x{EXPECTED_WORD:08X}",
                                   captured_observation=f"0x{captured_word:08X}")
        hardware_run.transition(HardwareState.HARDWARE_VERIFIED)
        state = hardware_run.state
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
        stderr = f"phase={phase}\n{failure}\n"
        if connection is not None and core_reload_succeeded:
            state = HardwareState.FAILED if not captured_words else HardwareState.RESULT_CAPTURED
        elif connection is not None and xous_write_committed:
            state = HardwareState.FAILED
        elif connection is not None:
            state = HardwareState.FAILED
        else:
            state = HardwareState.FAILED
    finally:
        if connection is not None:
            try:
                connection.close()
                log_lines.append("[host] Dabao CDC port closed")
            except Exception as close_error:
                stderr += f"close error: {type(close_error).__name__}: {close_error}\n"
        _DEVICE_LOCK.release()

    finished_at = _utc()
    manifest = {
        "run_id": run_id, "experiment_id": "dabao-fifo-probe",
        "experiment_title": "Dabao BIO FIFO0 sentinel probe",
        "mode": "HARDWARE", "adapter": "official-xous-bio-loader-protocol",
        "state": "COMPLETED" if state == HardwareState.HARDWARE_VERIFIED else "FAILED",
        "hardware_state": state.value,
        "evidence": state.value if state == HardwareState.HARDWARE_VERIFIED else
                    ("HARDWARE_EXECUTED" if core_reload_succeeded else "FAILED"),
        "started_at": started_epoch, "started_at_utc": started_at,
        "finished_at": time.time(), "finished_at_utc": finished_at,
        "duration_seconds": round(time.time() - started_epoch, 4),
        "exit_code": 0 if state == HardwareState.HARDWARE_VERIFIED else 1,
        "hardware_profile": {
            "profile_id": TARGET["profile_id"], "vid": TARGET["vid"], "pid": TARGET["pid"],
            "product": TARGET["product"], "serial": TARGET["serial"], "topology": TARGET["topology"],
            "persistent_port": TARGET["persistent_port"],
            "observed_linux_node": device.get("linux_device") if device else None,
        },
        "xous_version": XOUS_VERSION, "xous_source_revision": XOUS_REVISION,
        "experiment_source": str(BIO_SOURCE.relative_to(ROOT)),
        "experiment_source_sha256": _sha256(BIO_SOURCE) if BIO_SOURCE.exists() else None,
        "bio_binary": str(BIO_BINARY.relative_to(ROOT)), "bio_binary_size_bytes": len(image),
        "bio_binary_sha256": hashlib.sha256(image).hexdigest() if image else None,
        "bio_sim_source_revision": build.get("bio_sim_revision"),
        "bio_loader_source_revision": "a827a3c944c44c1b507e4eab55c76fc67871a8ca",
        "tool_versions": {"baud": BAUD, "data_bits": 8, "parity": "N", "stop_bits": 1},
        "operation_sequence": [
            "bio ready (console echo off; no persistent setting write)",
            "bio <base64(chunk-0)> (stage index 0; 64-byte code area; 44 zero pad bytes; CRC32)",
            "bio pad (zero-fill 59 remaining chunks; commit full 0xF00-byte image to Xous keystore)",
            "bio reload (initialize and start BIO core)",
            "bio rx 1 5 (read one FIFO0 word)",
            "close exact Dabao CDC port",
        ],
        "upload_protocol": {
            "decoded_chunk_bytes": CHUNK_WIRE_BYTES, "chunk_index": 0,
            "payload_bytes": CHUNK_BYTES, "program_bytes": len(image),
            "program_padding_bytes": CHUNK_BYTES - len(image),
            "remaining_zero_fill_chunks": MAX_CODE_BYTES // CHUNK_BYTES - 1,
            "crc32_be": f"0x{int.from_bytes(chunk[-4:], 'big'):08X}",
            "base64_sha256": hashlib.sha256(base64.b64encode(chunk)).hexdigest(),
        },
        "configuration": {
            "bio_clock_command_sent": False,
            "pin_configuration_command_sent": False,
            "stored_clock_behavior": "Xous reload uses the stored 1..350MHz BIO clock, else defaults to 350MHz.",
            "stored_pin_behavior": "Existing stored pin list is retained and reapplied by reload; no readback was found.",
            "program_gpio_calls": 0,
        },
        "expected_result": {"fifo": 0, "value": f"0x{EXPECTED_WORD:08X}"},
        "captured_fifo_words": [f"0x{word:08X}" for word in captured_words],
        "actual_result": {"value": f"0x{EXPECTED_WORD:08X}" if EXPECTED_WORD in captured_words else None,
                          "matches_expected": EXPECTED_WORD in captured_words},
        "xous_code_committed": xous_write_committed,
        "xous_commit_attempted": xous_commit_attempted,
        "bio_core_reload_succeeded": core_reload_succeeded,
        "failure": failure,
        "approval": {"required_phrase": APPROVAL_PHRASE, "provided": True},
        "known_limitations": [
            "Xous BIO console provides no readback command for a previously stored BIO image.",
            "A valid prior BIO program may already be running; staging does not stop it until bio reload.",
            "The existing pin configuration cannot be read through the documented BIO command interface and is reapplied by reload.",
            "This program emits no GPIO instructions; hardware run proves FIFO0 only, not a physical pad observation.",
        ],
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    (run_dir / "hardware-result.json").write_text(json.dumps({
        "evidence": manifest["evidence"], "expected": manifest["expected_result"],
        "actual": manifest["actual_result"], "captured_fifo_words": manifest["captured_fifo_words"],
        "xous_version": XOUS_VERSION, "device": manifest["hardware_profile"],
        "xous_code_committed": xous_write_committed, "core_reload_succeeded": core_reload_succeeded,
        "xous_commit_attempted": xous_commit_attempted,
        "failure": failure,
    }, indent=2) + "\n")
    stdout_path.write_text("\n".join(log_lines) + ("\n" if log_lines else ""))
    stderr_path.write_text(stderr)
    manifest["stdout_path"] = str(stdout_path.relative_to(ROOT)) if stdout_path.is_relative_to(ROOT) else str(stdout_path)
    manifest["stderr_path"] = str(stderr_path.relative_to(ROOT)) if stderr_path.is_relative_to(ROOT) else str(stderr_path)
    manifest["result_path"] = str((run_dir / "hardware-result.json").relative_to(ROOT)) if (run_dir / "hardware-result.json").is_relative_to(ROOT) else str(run_dir / "hardware-result.json")
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if failure:
        raise DabaoRunError(f"physical Dabao probe failed in phase {phase}; manifest saved at {run_dir / 'manifest.json'}: {failure}")
    return manifest
