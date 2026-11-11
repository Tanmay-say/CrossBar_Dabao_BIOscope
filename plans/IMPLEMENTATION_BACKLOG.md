# Implementation Backlog

## P0 — Immediate
1. **Repo audit:** inspect tree, branch, remotes, status, latest commit; verify whether Windows handoff commit exists. Deliver `reports/repo-audit.md`.
2. **Manjaro discovery:** run discovery script; report OS/kernel/CPU/RAM/disk/tools/USB/permissions. Deliver `docs/ENVIRONMENT_REPORT.md`.
3. **BIO-sim source review:** inspect README/build scripts/examples/CI; verify Linux dependencies and commands. Deliver `docs/TOOLCHAIN_PLAN.md`.
4. **BIO-sim baseline:** build/run smallest upstream example; record revision, versions, logs, exit code and artifacts.

## P1 — Product skeleton
5. Python host service: health endpoint, typed models, experiment registry, run-state model, mock adapter and tests.
6. React + TypeScript + Vite dashboard: overview, devices, experiments, runs, logs/artifacts; show mode explicitly.
7. Simulator integration: reviewed fixed commands, captured outputs, no arbitrary shell input.

## P2 — Hardware paths
8. Dabao/Xous feasibility and build-only example; document recovery.
9. M5Stick Plus2 minimal display/button firmware; build-only before flash.
10. Dynamic serial discovery, versioned protocol, tests with mock/pseudo-terminal.

## P3 — Integrated demo
11. M5Stick operator console.
12. Simulator experiment catalog and evidence.
13. Clean-checkout validation, secret scan, demo script, screenshots, logs and waveform.
