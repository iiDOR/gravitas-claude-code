#!/usr/bin/env python3
"""Gravitas Stop hook for Claude Code.
Blocks completion if unresolved tool failures exist in this session.
"""
import json, sys, os
from pathlib import Path


def session_dir(session_id: str) -> Path:
    return Path(os.getcwd()) / ".gravitas" / "sessions" / session_id


def load_failures(sdir: Path) -> list:
    fp = sdir / "failures.jsonl"
    if not fp.exists():
        return []
    failures = []
    for line in fp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            failures.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return failures


def load_evidence(sdir: Path) -> list:
    ev = sdir / "evidence.jsonl"
    if not ev.exists():
        return []
    entries = []
    for line in ev.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        print("{}")
        return

    session_id = payload.get("session_id", "")
    if not session_id:
        print("{}")
        return

    sdir = session_dir(session_id)
    if not sdir.exists():
        print("{}")
        return

    failures = load_failures(sdir)
    if not failures:
        print("{}")
        return

    # Check if a later PASS exists for any failing fingerprint
    evidence = load_evidence(sdir)
    passed_sources = {e.get("command", "") for e in evidence if e.get("verdict") == "PASS"}
    failed_fps = {f["fingerprint"] for f in failures if f.get("fingerprint")}

    # A failure is resolved if a subsequent PASS test_run/lint/type_check was observed
    has_pass = any(e.get("verdict") == "PASS" for e in evidence
                   if e.get("source") in ("test_run", "lint", "type_check"))

    if failed_fps and not has_pass:
        count = len(failed_fps)
        print(json.dumps({
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": (
                    f"Gravitas stop gate: {count} unresolved failure(s) this session. "
                    "Run tests or fix the failures before stopping. "
                    "(Invariant 4: never exact-retry; Invariant 3: completion needs evidence)"
                )
            }
        }))
        return

    print("{}")


if __name__ == "__main__":
    main()
