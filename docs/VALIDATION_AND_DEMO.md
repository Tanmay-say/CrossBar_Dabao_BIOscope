# Validation and Demo Checklist

## M0 Discovery
- [ ] Repo/Git state recorded.
- [ ] Manjaro system inventory recorded.
- [ ] USB descriptors collected read-only.
- [ ] Device identities confirmed or ambiguity documented.
- [ ] No serial ports opened, no flashing/writes.

## M1 Toolchain
- [ ] Current BIO-sim upstream requirements inspected.
- [ ] Linux support and exact versions verified.
- [ ] Manjaro package availability and sizes checked.
- [ ] User approval obtained before installation.

## M2 BIO-sim
- [ ] Upstream commit recorded.
- [ ] Minimal example compiles.
- [ ] Minimal simulation runs.
- [ ] Exit code/logs captured.
- [ ] Waveform generated if supported.
- [ ] Dashboard lists run and evidence.

## M3/M4 Hardware
- [ ] Dabao and M5Stick identities confirmed.
- [ ] Official target and recovery instructions verified.
- [ ] Build-only baseline succeeds.
- [ ] Explicit user approval for any flash.
- [ ] Hardware evidence captured and labeled.

## Demo story
1. Introduce BIOScope as an open-silicon programmable-I/O lab.
2. Show actual boards and independent USB connections.
3. Show device discovery.
4. Select and validate BIO experiment.
5. Run simulator and inspect logs/waveform.
6. Explain what simulation proves and does not prove.
7. Show physical execution only if verified and approved.
8. Close with reproducibility and observability.

Do not claim unsupported crypto, TRNG, secure-key, or bus-sniffing features.
