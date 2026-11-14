"""Validated PulseLink telemetry model and opt-in physical serial receiver.

Discovery is always sysfs/by-id only. The serial service is disabled unless
the host is explicitly launched with --enable-pulselink-serial, because CDC
open can reset the ESP32 and must never happen while Bruce is installed.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import json
import hashlib
import math
from pathlib import Path
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = 1
DEVICE = "m5stick-pulse-link"
VALID_STATES = {"waiting", "measuring", "complete", "timeout"}


class TelemetryError(ValueError):
    pass


def parse_telemetry(raw: bytes | str) -> dict:
    """Parse a single bounded JSON line and validate the complete v1 schema."""
    if isinstance(raw, bytes):
        if len(raw) > 2048:
            raise TelemetryError("telemetry frame exceeds 2048 bytes")
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TelemetryError("telemetry is not UTF-8") from exc
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > 2048:
        raise TelemetryError("telemetry frame exceeds 2048 bytes")
    try:
        item = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise TelemetryError("malformed telemetry JSON") from exc
    required = {"protocol", "device", "type", "sequence", "state", "pulse_count",
                "frequency_hz", "signal_level", "uptime_us", "edge_overflow", "edges"}
    if not isinstance(item, dict) or set(item) != required:
        raise TelemetryError("telemetry fields do not match protocol v1")
    if type(item["protocol"]) is not int or item["protocol"] != PROTOCOL or item["device"] != DEVICE or item["type"] != "telemetry":
        raise TelemetryError("unsupported PulseLink protocol or device")
    for key, maximum in (("sequence", 2**32-1), ("pulse_count", 10), ("uptime_us", 2**63-1)):
        value = item[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
            raise TelemetryError(f"invalid {key}")
    if not isinstance(item["state"], str) or item["state"] not in VALID_STATES:
        raise TelemetryError("invalid receiver state")
    if item["signal_level"] not in (0, 1) or isinstance(item["signal_level"], bool):
        raise TelemetryError("signal_level must be 0 or 1")
    if not isinstance(item["edge_overflow"], bool):
        raise TelemetryError("edge_overflow must be boolean")
    frequency = item["frequency_hz"]
    if frequency is not None:
        if isinstance(frequency, bool) or not isinstance(frequency, (int, float)):
            raise TelemetryError("frequency_hz must be numeric or null")
        if not math.isfinite(frequency) or not 0 < frequency <= 1000:
            raise TelemetryError("frequency_hz outside supported range")
        item["frequency_hz"] = float(frequency)
    edges = item["edges"]
    if not isinstance(edges, list) or len(edges) > 15:
        raise TelemetryError("edges must be a bounded list")
    normalized = []
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != {"timestamp_us", "level"}:
            raise TelemetryError("malformed edge record")
        stamp, level = edge["timestamp_us"], edge["level"]
        if isinstance(stamp, bool) or not isinstance(stamp, int) or not 0 <= stamp <= 2**32-1:
            raise TelemetryError("invalid edge timestamp")
        if isinstance(level, bool) or level not in (0, 1):
            raise TelemetryError("invalid edge level")
        normalized.append({"timestamp_us": stamp, "level": level})
    item["edges"] = normalized
    if item["state"] == "complete" and (item["pulse_count"] != 10 or item["signal_level"] != 0):
        raise TelemetryError("complete requires ten rising edges and a LOW input")
    return item


class PulseLinkStore:
    """Thread-safe latest real telemetry plus a measured-edge timeline."""
    def __init__(self, capture_root: Path | None = None):
        self._lock = threading.Lock()
        self.capture_root = capture_root
        self.latest = None
        self.last_seen = None
        self.connected = False
        self.error = None
        self.events = deque(maxlen=256)
        self.capture_id = None
        self.capture_start_uptime = None
        self.capture_started_at = None
        self.capture_edges = []
        self.capture_complete = False
        self.capture_overflow = False
        self.source = "LIVE_HARDWARE"

    def ingest(self, raw: bytes | str, now: datetime | None = None) -> dict:
        item = parse_telemetry(raw)
        now = now or datetime.now(timezone.utc)
        with self._lock:
            if self.latest and item["sequence"] <= self.latest["sequence"]:
                # MCU reboot resets uptime and sequence; recognize only a clear uptime reset.
                if item["uptime_us"] >= self.latest["uptime_us"]:
                    raise TelemetryError("duplicate or out-of-order telemetry sequence")
                self._reset_capture()
            if self.latest and item["uptime_us"] < self.latest["uptime_us"]:
                self._reset_capture()
            if self.capture_id is None:
                self.capture_id = str(uuid.uuid4())
                self.capture_start_uptime = item["uptime_us"]
                self.capture_started_at = now.timestamp()
                self.capture_edges = [{"timestamp_us": 0, "level": item["signal_level"], "kind": "initial"}]
            base = self.capture_start_uptime or item["uptime_us"]
            for edge in item["edges"]:
                delta = ((edge["timestamp_us"] - (item["uptime_us"] & 0xFFFFFFFF) + 2**31) & 0xFFFFFFFF) - 2**31
                # Edge timestamps are 32-bit micros(); signed delta maps them to
                # the adjacent 64-bit esp_timer_get_time() epoch.
                edge_uptime = max(0, item["uptime_us"] + delta)
                relative = max(0, edge_uptime - base)
                self.capture_edges.append({"timestamp_us": relative, "level": edge["level"], "kind": "edge"})
                self.events.append({"timestamp_us": edge_uptime, "level": edge["level"], "received_at": now.isoformat()})
            self.latest = item
            self.last_seen = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")
            self.connected = True
            self.capture_overflow = self.capture_overflow or item["edge_overflow"]
            self.error = "edge queue overflow; waveform capture is incomplete" if self.capture_overflow else None
            if item["state"] == "complete":
                levels = [event["level"] for event in self.capture_edges]
                rising = sum(1 for previous, current in zip(levels, levels[1:]) if previous == 0 and current == 1)
                falling = sum(1 for previous, current in zip(levels, levels[1:]) if previous == 1 and current == 0)
                ordered = all(a["timestamp_us"] <= b["timestamp_us"] for a, b in zip(self.capture_edges, self.capture_edges[1:]))
                self.capture_complete = (levels[0] == 0 and levels[-1] == 0 and rising == 10 and falling == 10 and ordered and not self.capture_overflow)
                if self.capture_complete and self.capture_root:
                    self._write_vcd_locked()
        return item

    def _reset_capture(self):
        self.capture_id = None
        self.capture_start_uptime = None
        self.capture_started_at = None
        self.capture_edges = []
        self.capture_complete = False
        self.capture_overflow = False

    def disconnect(self, error: str | None = None):
        with self._lock:
            self.connected = False
            self.error = error

    def reject_frame(self, error: str):
        with self._lock:
            self.error = error

    def snapshot(self, now: float | None = None) -> dict:
        with self._lock:
            connected = self.connected
            if self.last_seen:
                seen = datetime.fromisoformat(self.last_seen.replace("Z", "+00:00")).timestamp()
                connected = connected and (time.time() if now is None else now) - seen <= 2.0
            trace = None
            if self.capture_complete and self.capture_id and self.capture_root:
                trace_path = self.capture_root / self.capture_id / "pulselink.vcd"
                if trace_path.is_file():
                    trace = {"run_id": self.capture_id,
                             "path": str(trace_path.relative_to(ROOT)),
                             "size_bytes": trace_path.stat().st_size,
                             "evidence": "LIVE_HARDWARE"}
            return {
                "mode": "LIVE_HARDWARE" if connected else "NOT_CONNECTED",
                "connected": connected,
                "device": "M5StickC Plus2 receiver" if connected else None,
                "source": self.source,
                "state": self.latest["state"] if self.latest and connected else "disconnected",
                "telemetry": self.latest if connected else None,
                "last_seen": self.last_seen,
                "events": list(self.events),
                "error": self.error,
                "capture": trace,
                "capture_complete": self.capture_complete,
            }

    def _write_vcd_locked(self):
        # VCD records only actual GPIO32 transitions received from MCU interrupts.
        if not self.capture_id or len(self.capture_edges) < 3:
            return
        run = self.capture_root / self.capture_id
        run.mkdir(parents=True, exist_ok=True)
        path = run / "pulselink.vcd"
        lines = ["$date BIOScope recorded hardware capture $end", "$version BIOScope PulseLink v1 $end",
                 "$timescale 1 us $end", "$scope module m5stick $end",
                 "$var wire 1 ! gpio32 $end", "$upscope $end", "$enddefinitions $end"]
        for edge in self.capture_edges:
            lines.extend((f"#{edge['timestamp_us']}", f"{edge['level']}!"))
        path.write_text("\n".join(lines) + "\n")
        now = time.time()
        started = self.capture_started_at or now
        relative_path = str(path.relative_to(ROOT))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = {"run_id": self.capture_id, "experiment_id": "pulselink_signal_generator",
                    "experiment_title": "BIOscope PulseLink physical pulse capture",
                    "mode": "HARDWARE", "state": "COMPLETED", "evidence": "LIVE_HARDWARE", "exit_code": 0,
                    "started_at": started, "finished_at": now, "duration_seconds": round(now-started, 4),
                    "source": "M5Stick GPIO32 interrupt timestamps",
                    "actual_pulse_count": self.latest["pulse_count"], "measured_frequency_hz": self.latest["frequency_hz"],
                    "signal_level": self.latest["signal_level"], "edges": len(self.capture_edges)-1,
                    "stdout": "", "stderr": "", "vcd_path": relative_path, "vcd_sha256": digest,
                    "artifacts":[{"name":"pulselink.vcd", "path":relative_path, "type":"vcd-waveform",
                                  "verified":True, "evidence":"LIVE_HARDWARE", "size_bytes":path.stat().st_size, "sha256":digest}]}
        (run / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


class PulseLinkSerialService:
    """Optional actual USB serial reader; never enabled implicitly."""
    def __init__(self, store: PulseLinkStore, by_id: Path | None = None):
        from device_discovery import BY_ID
        self.store = store
        self.by_id = by_id or BY_ID
        self.stop_event = threading.Event()
        self.thread = None
        self.serial_port = None
        self.state = "DISABLED"

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.state = "SEARCHING"
        self.thread = threading.Thread(target=self._worker, name="pulselink-serial", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        port = self.serial_port
        if port:
            try: port.close()
            except OSError: pass
        if self.thread:
            self.thread.join(timeout=2)
        self.state = "DISABLED"
        self.store.disconnect("serial service stopped")

    def _worker(self):
        from device_discovery import PROFILES, discover
        profile = next(p for p in PROFILES if p["id"] == "m5stick")
        expected = str(self.by_id / profile["expected_by_id"])
        while not self.stop_event.is_set():
            inventory = discover(by_id_dir=self.by_id)
            device = next((d for d in inventory if d["id"] == "m5stick"), None)
            if not device or not device["connected"] or not device["serial_link_available"]:
                self.state = "WAITING_FOR_DEVICE"
                self.store.disconnect("verified M5Stick profile or by-id path unavailable")
                self.stop_event.wait(1)
                continue
            if device["persistent_port"] != expected or device["serial"] != profile["serial"]:
                self.state = "IDENTITY_REJECTED"
                self.store.disconnect("M5Stick identity profile changed")
                self.stop_event.wait(1)
                continue
            try:
                import serial
                self.state = "OPENING"
                # This is intentionally reachable only with the explicit host CLI flag.
                port = serial.Serial(port=None, baudrate=115200, timeout=0.25, write_timeout=0.25,
                                     exclusive=True)
                port.dtr = False
                port.rts = False
                port.port = expected
                port.open()
                self.serial_port = port
                self.state = "CONNECTED"
                last_heartbeat = 0.0
                while not self.stop_event.is_set():
                    if time.monotonic() - last_heartbeat >= 1.0:
                        port.write(b'{"protocol":1,"type":"host_heartbeat"}\n')
                        last_heartbeat = time.monotonic()
                    line = port.readline()
                    if not line:
                        snap = self.store.snapshot()
                        if snap.get("last_seen"):
                            last = datetime.fromisoformat(snap["last_seen"].replace("Z", "+00:00")).timestamp()
                            if time.time() - last > 2:
                                self.store.disconnect("telemetry timeout")
                        continue
                    try:
                        try:
                            hello = json.loads(line)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            hello = None
                        if isinstance(hello, dict) and hello.get("type") == "hello":
                            if hello.get("protocol") != PROTOCOL or hello.get("device") != DEVICE:
                                raise TelemetryError("receiver hello identity/version mismatch")
                            self.state = "STREAMING"
                            continue
                        self.store.ingest(line)
                    except TelemetryError as exc:
                        self.store.reject_frame(f"rejected telemetry: {exc}")
            except Exception as exc:
                self.state = "DISCONNECTED"
                self.store.disconnect(f"serial disconnected or unavailable: {type(exc).__name__}")
                time.sleep(0.5)
            finally:
                if self.serial_port:
                    try: self.serial_port.close()
                    except OSError: pass
                    self.serial_port = None
