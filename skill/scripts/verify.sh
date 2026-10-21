#!/usr/bin/env bash
# GRAVITAS Verification Shell Engine
set -e

if [ -f "scripts/verify.py" ]; then
    python3 scripts/verify.py "$@"
elif command -v python &>/dev/null; then
    python scripts/verify.py "$@"
else
    echo "VERDICT: FAIL -- Python runner required"
    exit 1
fi
