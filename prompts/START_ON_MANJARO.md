# Codex kickoff — BIOScope on Manjaro

You are taking over BIOScope development on my Manjaro Linux PC.

## Read first
Read README, `.agents/skills/bioscope-engineer/SKILL.md`, all docs, plans/IMPLEMENTATION_BACKLOG.md, progress/STATUS.md and progress/ACTIVITY_LOG.md.

## Goal
Build BIOScope for Baochip-1x Dabao + M5Stack M5StickC Plus2. It is an open-silicon hardware security and programmable-I/O lab. Dabao is target silicon; M5Stick is operator UI; Manjaro PC is host/orchestrator. Both boards connect independently over USB.

## First phase — read-only
1. Inspect pwd, repo tree, .git, branch, remotes, latest commit and git status.
2. Do not assume Windows handoff was pushed; verify actual history and remote.
3. If this folder is only the starter kit and not the real repo, do not create an unrelated repo or overwrite work. Tell me what repo must be opened/cloned.
4. Run `bash scripts/discover-manjaro.sh`.
5. Create `docs/ENVIRONMENT_REPORT.md` from actual observations.
6. Identify boards only from evidence. If ambiguous, ask me to unplug/replug one at a time.
7. Read current upstream BIO-sim README, scripts, examples and CI. Verify exact Linux dependencies, versions and commands.
8. Create `docs/TOOLCHAIN_PLAN.md` with package source, versions, availability, download/installed sizes and exact proposed commands.
9. Update status and activity log.

## Work priority
M0 repo + Manjaro discovery. M1 BIO-sim toolchain verification. M2 smallest BIO-sim build/simulation and waveform if supported. Then audit/build host bridge and dashboard. Then verify Dabao/Xous and M5Stick firmware.

## Language boundaries
- BIO source: C according to official BIO workflow.
- Dabao/Xous apps: Rust only where upstream supports it.
- M5Stick firmware: C/C++ with verified Plus2 framework.
- Host: Python.
- Dashboard: TypeScript/React/Vite.

## Hard constraints
- No jumper wires, breadboard, modules or external sensors.
- No direct board-to-board connection.
- No Docker or WSL requirement.
- Do not open serial ports during read-only discovery.
- Do not mount/write Dabao update volume.
- Do not flash, erase or change bootloader/firmware.
- Do not install packages, use AUR, change groups/udev, or make privileged changes without asking.
- Do not delete caches or user data.
- Do not push/publish/deploy or rewrite Git history without approval.
- No secrets or generated binaries in Git.

## Evidence
Use NOT RUN, BLOCKED, COMPILE_ONLY, SIMULATED, HARDWARE EXECUTED, HARDWARE VERIFIED. A compile is not a simulation; a simulation is not hardware verification.

## Report and stop
Report repo/commit, Manjaro system and disk, USB inventory and confidence, toolchain table, upstream BIO-sim requirements, proposed install plan/space, blockers, and the single next safe action. STOP before installing anything or touching firmware. Wait for my approval.
