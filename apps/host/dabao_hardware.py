"""Evidence-aware Dabao BIO capability and operation planning.

This module deliberately contains no serial opener. Planning a run is read-only;
the official loader persists BIO code/configuration in the Dabao keystore, so a
physical transport requires a separate, explicit operator approval.
"""
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
import json

from device_discovery import discover

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_LOADER_REVISION = "a827a3c944c44c1b507e4eab55c76fc67871a8ca"
SUPPORTED_HARDWARE_EXPERIMENTS = frozenset({"dabao-fifo-probe"})
VERIFIED_RUN_ID = "d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62"


class HardwareState(StrEnum):
    DISCOVERED = "DISCOVERED"
    CAPABILITY_CHECK = "CAPABILITY_CHECK"
    VALIDATING = "VALIDATING"
    BUILDING = "BUILDING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    READY = "READY"
    EXECUTING = "EXECUTING"
    RESULT_CAPTURED = "RESULT_CAPTURED"
    HARDWARE_VERIFIED = "HARDWARE_VERIFIED"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"


TRANSITIONS = {
    HardwareState.DISCOVERED: {HardwareState.CAPABILITY_CHECK, HardwareState.FAILED},
    HardwareState.CAPABILITY_CHECK: {HardwareState.VALIDATING, HardwareState.UNSUPPORTED, HardwareState.FAILED},
    HardwareState.VALIDATING: {HardwareState.BUILDING, HardwareState.AWAITING_APPROVAL, HardwareState.UNSUPPORTED, HardwareState.FAILED},
    HardwareState.BUILDING: {HardwareState.READY, HardwareState.AWAITING_APPROVAL, HardwareState.FAILED},
    HardwareState.AWAITING_APPROVAL: {HardwareState.READY, HardwareState.FAILED},
    HardwareState.READY: {HardwareState.EXECUTING, HardwareState.FAILED},
    HardwareState.EXECUTING: {HardwareState.RESULT_CAPTURED, HardwareState.FAILED},
    HardwareState.RESULT_CAPTURED: {HardwareState.HARDWARE_VERIFIED, HardwareState.FAILED},
    HardwareState.HARDWARE_VERIFIED: set(),
    HardwareState.FAILED: set(),
    HardwareState.UNSUPPORTED: set(),
}


@dataclass
class HardwareRun:
    """Typed hardware run lifecycle; successful process exit alone is not proof."""
    experiment_id: str
    state: HardwareState = HardwareState.DISCOVERED
    evidence: str = "NOT RUN"
    expected_observation: str | None = None
    captured_observation: str | None = None

    def transition(self, next_state):
        next_state = HardwareState(next_state)
        if next_state not in TRANSITIONS[self.state]:
            raise ValueError(f"invalid hardware run transition: {self.state} -> {next_state}")
        if next_state == HardwareState.RESULT_CAPTURED:
            if not self.captured_observation:
                raise ValueError("hardware result requires an actual target response")
            self.evidence = "HARDWARE_EXECUTED"
        if next_state == HardwareState.HARDWARE_VERIFIED:
            if not self.expected_observation or self.captured_observation != self.expected_observation:
                raise ValueError("hardware verification requires captured response equal to the expected value")
            self.evidence = "HARDWARE_VERIFIED"
        self.state = next_state
        return self.state


@dataclass(frozen=True)
class DabaoCapabilityReport:
    profile_id: str
    connected: bool
    identity_verified: bool
    serial_link_available: bool
    hardware_firmware: str
    bio_console: str
    bio_loader_revision: str
    execution_state: HardwareState
    physical_execution_enabled: bool
    reason: str

    def as_dict(self):
        return {**self.__dict__, "execution_state": self.execution_state.value}


def capabilities(devices=None):
    devices = devices if devices is not None else discover()
    dabao = next((d for d in devices if d.get("id") == "dabao"), None)
    persistent = dabao.get("persistent_port") if dabao else None
    matched = bool(dabao and dabao.get("connected") and
                   dabao.get("vid") == "1d50" and dabao.get("serial") == "TLZ4A6" and
                   dabao.get("usb_topology") == "1-4" and
                   dabao.get("observed_product") == "Dabao" and
                   persistent and Path(persistent).name == "usb-Baochip_Dabao_TLZ4A6-if02")
    built = ROOT / "artifacts/builds/dabao_fifo_probe/manifest.json"
    build_evidence = "compiled and errata-checked" if built.is_file() else "not built"
    verified = None
    manifest_path = ROOT / "artifacts/runs" / VERIFIED_RUN_ID / "manifest.json"
    if manifest_path.is_file():
        try:
            candidate = json.loads(manifest_path.read_text())
            expected = candidate.get("expected_result", {}).get("value")
            actual = candidate.get("actual_result", {}).get("value")
            profile = candidate.get("hardware_profile", {})
            if (candidate.get("evidence") == "HARDWARE_VERIFIED" and expected == actual == "0xB105C0DE" and
                    profile.get("serial") == "TLZ4A6" and profile.get("vid") == "1d50" and profile.get("pid") == "6197"):
                verified = {"run_id": candidate["run_id"], "evidence": candidate["evidence"],
                            "started_at_utc": candidate.get("started_at_utc"), "expected": expected,
                            "actual": actual, "xous_version": candidate.get("xous_version"),
                            "device_serial": profile.get("serial")}
        except (OSError, ValueError, KeyError):
            verified = None
    report = DabaoCapabilityReport(
        profile_id="dabao", connected=bool(dabao and dabao.get("connected")),
        identity_verified=matched,
        serial_link_available=bool(dabao and dabao.get("serial_link_available")),
        hardware_firmware=(f"Xous {verified['xous_version']} (run evidence)" if verified else "UNVERIFIED (no verified run)"),
        bio_console=("Official BIO console performed one verified FIFO0 probe" if verified else
                     "Official Xous dabao-console BIO REPL documented; installed app version unverified"),
        bio_loader_revision=UPSTREAM_LOADER_REVISION,
        execution_state=HardwareState.CAPABILITY_CHECK if matched and build_evidence != "not built" else HardwareState.UNSUPPORTED,
        physical_execution_enabled=False,
        reason=(f"Probe {build_evidence}. Official loader uploads BIO bytes into Xous keystore and reload starts the BIO core. "
                + (f"A verified physical FIFO0 result is recorded in run {verified['run_id']}. This one-shot probe is consumed and further execution is locked. "
                   if verified else "No verified physical BIO operation is recorded. ")
                + "Upload can replace an existing stored BIO program."),
    )
    result = report.as_dict()
    result["last_verified_run"] = verified
    return result


def prepare_execution_request(experiment_id, devices=None):
    """Create a non-executing approval request from the strict experiment allow-list."""
    if experiment_id not in SUPPORTED_HARDWARE_EXPERIMENTS:
        raise ValueError("experiment is not allow-listed for Dabao hardware")
    report = capabilities(devices)
    if not report["identity_verified"]:
        raise RuntimeError("exact Dabao identity is not currently verified")
    binary_manifest_path = ROOT / "artifacts/builds/dabao_fifo_probe/manifest.json"
    if not binary_manifest_path.is_file():
        raise RuntimeError("target BIO binary is not built")
    build_manifest = json.loads(binary_manifest_path.read_text())
    return {
        "target": {"profile_id": "dabao", "vid": "1d50", "pid": "6197", "serial": "TLZ4A6", "topology": "1-4",
                   "persistent_port": "usb-Baochip_Dabao_TLZ4A6-if02"},
        "experiment_id": experiment_id,
        "binary": build_manifest["binary"],
        "binary_sha256": build_manifest["binary_sha256"],
        "evidence": "NOT RUN",
        "state": HardwareState.CAPABILITY_CHECK.value,
        "required_preflight_after_operator_approval": [
            "Open only the exact Dabao CDC link and send documented read-only `ver xous` to identify the running Xous version",
        ],
        "physical_write_plan_after_separate_approval": [
            "Open the exact Dabao CDC ACM persistent link at 1000000 baud 8N1",
            "Send documented bio-loader readiness exchange",
            "Upload the 20-byte BIO image and zero-pad the remaining BIO image slots",
            "Persist the image in Xous keystore and issue bio reload to start the BIO core",
            "Issue documented bio rx 1 5 and capture FIFO0 output",
        ],
        "expected_target_response": "0xb105c0de from the BIO FIFO0 receive path",
        "physical_write_approval_required": True,
        "side_effects": [
            "The loader replaces the previously stored BIO program in the Xous keystore.",
            "BIO core state changes and the new program is started.",
            "Opening the USB CDC port can change host modem-control lines; reset behavior is not verified for this board.",
        ],
        "limitations": [
            "No backed-up readback path for an existing stored BIO image has been verified.",
            "Current Dabao console/app version is unknown; command support is documented upstream, not confirmed on this unit.",
            "No physical GPIO is touched; this experiment proves only a BIO core FIFO response.",
        ],
        "bio_loader_revision": UPSTREAM_LOADER_REVISION,
    }
