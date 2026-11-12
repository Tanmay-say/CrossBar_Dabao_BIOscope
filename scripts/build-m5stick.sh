#!/usr/bin/env bash
set -euo pipefail
BIOSCOPE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PLATFORMIO_CORE_DIR="$BIOSCOPE_ROOT/.cache/platformio"
exec "$BIOSCOPE_ROOT/.venv/bin/pio" run --project-dir "$BIOSCOPE_ROOT/firmware/m5stick-plus2" -e m5stack-stickc-plus2
