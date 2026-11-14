#!/usr/bin/env python3
"""Stage approved PulseLink code/config on Dabao without reloading/executing."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/host"))
from dabao_pulselink import stage_pulselink  # noqa: E402

APPROVAL = "STAGE_PULSELINK_BIO1_7000HZ_NO_RELOAD_TLZ4A6"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", required=True, help="explicitly authorize target BIO/config keystore writes")
    args = parser.parse_args()
    if args.approval != APPROVAL:
        parser.error("no serial port opened; exact PulseLink staging authorization phrase required")
    print(json.dumps(stage_pulselink(), indent=2))

if __name__ == "__main__":
    main()
