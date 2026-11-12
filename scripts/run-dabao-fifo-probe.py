#!/usr/bin/env python3
"""The one-time physical Dabao FIFO0 probe has already been completed."""
import sys


def main():
    print(
        "Physical Dabao FIFO0 probe is locked after the verified run; "
        "this command will not discover or open a device.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
