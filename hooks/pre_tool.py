#!/usr/bin/env python3
"""Gravitas PreToolUse hook for Claude Code.
Enforces read-before-write: deny writes to existing files not yet read this session.
"""
import json, sys, os
from pathlib import Path

WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}


def session_dir(session_id: str) -> Path:
    return Path(os.getcwd()) / ".gravitas" / "sessions" / session_id


def load_reads(sdir: Path) -> set:
    ev = sdir / "evidence.jsonl"
    if not ev.exists():
        return set()
    reads = set()
    for line in ev.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            if e.get("source") == "read" and e.get("file"):
                reads.add(os.path.normcase(os.path.abspath(e["file"])))
        except json.JSONDecodeError:
            pass
    return reads


def target_path(tool_name: str, tool_input: dict) -> str | None:
    return tool_input.get("file_path")


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    session_id = payload.get("session_id", "")

    if tool_name not in WRITE_TOOLS or not session_id:
        sys.exit(0)

    target = target_path(tool_name, tool_input)
    if not target or not os.path.exists(target):
        sys.exit(0)  # new file — no prior read required

    abs_target = os.path.normcase(os.path.abspath(target))
    sdir = session_dir(session_id)
    reads = load_reads(sdir)

    if abs_target not in reads:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Gravitas read-before-write: read {target} before editing it. "
                    "(Invariant 1: ground before mutating)"
                )
            }
        }))


if __name__ == "__main__":
    main()
