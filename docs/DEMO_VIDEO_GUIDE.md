# BIOScope demo video guide (3–5 minutes)

## Before recording

1. Connect the Dabao and M5Stick to the Manjaro PC using their normal USB cables. Do not open serial consoles or run hardware operations.
2. Start the API and dashboard using [`GETTING_STARTED.md`](GETTING_STARTED.md).
3. Confirm `/api/health` and `/api/devices` respond. The inventory call reads descriptors only.
4. Open the existing physical run `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`. Do not execute it again.
5. Have the existing blink FST available at `artifacts/runs/ad1120e1-3214-4e7d-b334-20f84e28c15b/trace.fst` and GTKWave installed.
6. Frame the devices so serial labels are not legible in the public video. Do not show secrets, private host paths, or the mounted update volume.

## Shot list and narration

### 0:00–0:25 — Opening and purpose

**Picture:** Medium shot of the Manjaro laptop with Dabao beside it. M5Stick is visible but its screen can remain on Bruce's normal screen.

**Say:** “This is BIOScope, a small lab for exploring Baochip programmable I/O. The Manjaro host keeps simulation and physical evidence separate: BIO-sim provides repeatable RTL traces, and the Dabao record shown here is a completed physical FIFO test.”

**Proves:** The project and actual hardware are present; no live hardware command is implied.

### 0:25–0:55 — Host and dashboard

**Picture:** Dashboard Overview in the browser at `http://127.0.0.1:5173`; optionally show the backend terminal briefly with the server listening on port 8765.

**Command (Terminal 3):**

```bash
curl -fsS http://127.0.0.1:8765/api/health
```

**Say:** “The browser is using the local Python API. The API health response and dashboard are live, while the run records below remain immutable evidence.”

**Proves:** Frontend-to-backend connectivity.

### 0:55–1:25 — Device discovery

**Picture:** Hardware Devices page, then a short camera view of Dabao and M5Stick separately connected to the PC. Keep identifiers readable only if public disclosure is intended.

**Command (optional):**

```bash
curl -fsS http://127.0.0.1:8765/api/devices
```

**Say:** “Discovery reads USB descriptors and persistent device links without opening serial ports. Dabao is identified by a compound profile. The other USB entry is a QinHeng serial bridge associated with the M5Stick; the descriptors do not prove the board model. Bruce remains installed and BIOScope does not claim a Bruce protocol connection.”

**Proves:** Read-only current discovery and honest device attribution.

### 1:25–2:20 — Physical Dabao result record

**Picture:** Run History, select `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`, show its evidence label, expected/actual FIFO0 value and captured log. Do not click any execute/run control.

**Command (optional):**

```bash
curl -fsS http://127.0.0.1:8765/api/runs/d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62
```

**Say:** “This is the recorded physical run, not a new live run. The approved pin-free BIO probe returned FIFO0 value `0xB105C0DE`, matching the expected sentinel. Its source and 20-byte image hashes, Xous revision, result and console log are recorded. The loader replaced the stored BIO program, and there is no documented readback backup; therefore I will not repeat it for this recording.”

**Proves:** One genuine physical FIFO result and its provenance; it does not prove GPIO pad output.

### 2:20–2:55 — Manifest and evidence provenance

**Picture:** Open the manifest/result in the dashboard or show the sanitized [`hardware-evidence/public/`](hardware-evidence/public/) directory. Do not show the raw manifest containing private identifiers.

**Command:**

```bash
sha256sum docs/hardware-evidence/public/{manifest.json,hardware-result.json,stdout.log,stderr.log,amendment.json}
```

**Say:** “The repository contains a public sanitized evidence copy with its own integrity index. Local raw evidence remains unchanged and ignored. Device serials, host paths, the approval phrase and echoed upload payload are redacted from the public copy.”

**Proves:** Reproducible public evidence and explicit redactions.

### 2:55–3:45 — Simulation and waveform

**Picture:** Open the existing blink FST in GTKWave, expand the relevant top-level GPIO signals and display GPIO 21 transitions. Keep the API run output or dashboard available to show this is the `blink` simulation.

**Command:**

```bash
gtkwave artifacts/runs/ad1120e1-3214-4e7d-b334-20f84e28c15b/trace.fst
```

**Say:** “This waveform is from BIO-sim, not from physical GPIO probing. The simulator run records GPIO 21 transitions and a genuine FST. The two evidence types complement each other but are not interchangeable.”

**Proves:** GTKWave can inspect the real simulator artifact; no physical pin claim is made.

### 3:45–4:10 — M5Stick and close

**Picture:** Show the M5Stick running its unchanged Bruce firmware next to the dashboard, then return to the overview and physical run card.

**Say:** “The M5Stick is part of the intended operator architecture, but Bruce does not implement BIOScope's versioned JSON request protocol and no safe Bruce exchange has been verified. It is shown here as the preserved operator device, not as a live BIOScope controller. A custom BIOScope firmware migration would need a separate backup/recovery review and explicit approval.”

**Closing:** Return to the Dabao run record and leave the `HARDWARE_VERIFIED` label and `0xB105C0DE` result visible. State that the only physical operation shown was completed earlier and is not repeated.

## Recording integrity

- Do not run the Dabao probe CLI, serial version query, M5Stick bridge, or any upload/reload command.
- Do not label the blink FST as physical evidence.
- Do not imply that the M5Stick sent an API request.
- Do not show raw private evidence files, approval text, USB serial numbers, personal paths, or the update volume.
- If the browser/API cannot show live data, stop and fix the startup issue; do not substitute a still image or fabricated result.
