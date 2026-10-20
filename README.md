# gravitas-claude-code

Gravitas engineering reliability runtime for **Claude Code**.

Enforces three invariants via hooks, on every session, automatically:

| # | Invariant | Mechanism |
|---|-----------|-----------|
| 1 | **Read before mutating** | `PreToolUse` blocks `Write`/`Edit` on files not yet read this session |
| 3 | **Completion needs evidence** | `PostToolUse` logs reads, writes, failures, and test verdicts per session |
| 4 | **Never exact-retry a failure** | `Stop` gate blocks session end if failures are unresolved |

Invariants 2 and 5 (scope gate, acceptance criteria) are available via `contract.json` — see the skill docs.

---

## Install

```
npx gravitas-claude-code --yes
```

Or interactive (prompts before installing):

```
npx gravitas-claude-code
```

Restart Claude Code after install. The `/gravitas` slash command becomes available immediately.

---

## What gets installed

```
~/.claude/skills/gravitas/     ← /gravitas skill (SKILL.md + agents + references + resources)
~/.claude/hooks/gravitas/      ← pre_tool.py, post_tool.py, stop_gate.py
~/.claude/settings.json        ← PreToolUse, PostToolUse, Stop hooks wired (existing hooks preserved)
```

---

## Evidence log

Per-session evidence is written to `.gravitas/sessions/<session-id>/`:

```
evidence.jsonl   — reads, writes, test verdicts
failures.jsonl   — tool failures with fingerprints
```

---

## Credit

Ported from [udaysharmadev/Gravitas](https://github.com/udaysharmadev/Gravitas) — the original Antigravity runtime.  
Claude Code adaptation by [iiDOR](https://github.com/iiDOR).

## License

MIT
