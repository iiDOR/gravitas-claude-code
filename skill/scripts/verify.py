#!/usr/bin/env python3
"""Gravitas Standalone Verification Runner for Claude Code.

Discovers project validators (checking .gravitas/knowledge/test-matrix.md first,
then detecting project files), executes the test command, captures output,
and emits authoritative VERDICT: PASS or VERDICT: FAIL.
"""
import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

def detect_project(root: Path):
    # Check .gravitas/knowledge/test-matrix.md first
    test_matrix = root / ".gravitas" / "knowledge" / "test-matrix.md"
    if test_matrix.exists():
        try:
            content = test_matrix.read_text(encoding="utf-8")
            m = re.search(r"-\s*\*\*(?:Unit.*?Suite|Unit Tests)\*\*:\s*`([^`]+)`", content, re.IGNORECASE)
            if m and m.group(1).strip() and not m.group(1).strip().startswith("["):
                candidate = m.group(1).strip()
                if candidate != "python scripts/verify.py":
                    return candidate
        except Exception:
            pass

    if (root / "package.json").exists():
        pkg = json.loads((root / "package.json").read_text(encoding="utf-8", errors="ignore"))
        scripts = pkg.get("scripts", {})
        if "test" in scripts:
            return "npm test"
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "vitest" in deps:
            return "npx vitest run"
        if "jest" in deps:
            return "npx jest"
        return "npx tsc --noEmit"
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        return "python -m pytest -v"
    if (root / "Cargo.toml").exists():
        return "cargo test"
    if (root / "go.mod").exists():
        return "go test ./..."
    if (root / "CMakeLists.txt").exists():
        return "ctest --output-on-failure"
    return "echo 'No test runner discovered'"

def run_cmd(command: str):
    print(f"Executing: {command}")
    print("-" * 60)
    try:
        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        output = res.stdout + res.stderr
        print(output)
        print("-" * 60)
        return (res.returncode == 0, output)
    except subprocess.TimeoutExpired:
        print("ERROR: Execution timed out after 300s")
        return (False, "Timeout expired")
    except Exception as e:
        print(f"ERROR: {e}")
        return (False, str(e))

def main():
    parser = argparse.ArgumentParser(description="Gravitas Verifier")
    parser.add_argument("--cmd", help="Override test command")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    root = Path.cwd()
    cmd = args.cmd or detect_project(root)

    success, output = run_cmd(cmd)

    if args.json:
        res = {
            "command": cmd,
            "success": success,
            "verdict": "PASS" if success else "FAIL"
        }
        print(json.dumps(res, indent=2))
    else:
        if success:
            print("VERDICT: PASS")
        else:
            print("VERDICT: FAIL -- test command exited with non-zero status")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
