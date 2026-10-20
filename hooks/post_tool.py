#!/usr/bin/env python3
"""Gravitas PostToolUse hook for Claude Code.
Logs reads, writes, failures, and test runs to .gravitas/sessions/<id>/evidence.jsonl.
"""
import json, sys, os, hashlib
from datetime import datetime, timezone
from pathlib import Path

READ_TOOLS = {"Read", "Glob", "Grep"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}

TEST_TERMS = ["vitest", "pytest", "jest", "go test", "cargo test", "rspec", "dotnet test", "mvn test"]
LINT_TERMS = ["eslint", "ruff", "clippy", "rubocop"]
TYPE_TERMS = ["tsc --noEmit", "mypy", "cargo check"]


def session_dir(session_id: str) -> Path:
    sdir = Path(os.getcwd()) / ".gravitas" / "sessions" / session_id
    sdir.mkdir(parents=True, exist_ok=True)
    return sdir


def append_evidence(sdir: Path, entry: dict) -> None:
    with open(sdir / "evidence.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def fingerprint(tool_name: str, tool_input: dict) -> str:
    key = json.dumps({"tool": tool_name, "input": tool_input}, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        print("{}")
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    tool_response = payload.get("tool_response", "")
    success = payload.get("success", True)
    session_id = payload.get("session_id", "")
    ts = datetime.now(timezone.utc).isoformat()

    if not session_id:
        print("{}")
        return

    sdir = session_dir(session_id)

    if tool_name in READ_TOOLS:
        path = tool_input.get("file_path", tool_input.get("pattern", ""))
        if path:
            append_evidence(sdir, {
                "source": "read",
                "file": str(os.path.abspath(path)),
                "timestamp": ts,
            })

    if tool_name in WRITE_TOOLS:
        path = tool_input.get("file_path", "")
        append_evidence(sdir, {
            "source": "write",
            "file": str(os.path.abspath(path)) if path else "",
            "success": success,
            "timestamp": ts,
        })

    if not success:
        fp = fingerprint(tool_name, tool_input)
        with open(sdir / "failures.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "tool": tool_name,
                "fingerprint": fp,
                "error": str(tool_response)[:500],
                "timestamp": ts,
            }) + "\n")

    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        source = next((k for k, terms in {
            "test_run": TEST_TERMS,
            "lint": LINT_TERMS,
            "type_check": TYPE_TERMS,
        }.items() if any(t in cmd for t in terms)), None)
        if source:
            append_evidence(sdir, {
                "source": source,
                "command": cmd,
                "success": success,
                "verdict": "PASS" if success else "FAIL",
                "timestamp": ts,
            })

    print("{}")


if __name__ == "__main__":
    main()
