# gravitas-claude-code

Gravitas engineering reliability runtime & **Living Knowledge Engine** for **Claude Code**.

Enforces invariants via hooks and persistent repository memory, on every session, automatically:

| # | Invariant | Mechanism |
|---|-----------|-----------|
| 0 | **Ground in knowledge first, synchronize on mutation** | `Living Knowledge Engine` (`scripts/knowledge.py`) eliminates blind recon & saves ~90% tokens |
| 1 | **Read before mutating** | `PreToolUse` hook blocks `Write`/`Edit` on files not yet read this session |
| 2 | **Stay in declared scope** | Guarded write boundaries via `contract.json` / `<task_contract>` |
| 3 | **Completion needs evidence** | `PostToolUse` logs reads, writes, failures, and test verdicts per session |
| 4 | **Never exact-retry a failure** | `Stop` gate blocks session end if failures are unresolved |
| 5 | **Satisfy the contract** | Acceptance criteria verification via deterministic validators |
| 6 | **Say what you cannot verify** | Anti-hallucination calibration & confidence downgrading |

---

## What's New: The Living Knowledge Engine (GKE)

Traditional coding agents waste **40,000 to 80,000 tokens** per turn searching and reading dozens of files repeatedly.

Gravitas solves this with a machine-readable, persistent knowledge substrate stored in `.gravitas/knowledge/`:
- **`init`**: Scans the project, maps topology, and bootstraps `architecture.md`, `conventions.md`, and `test-matrix.md`.
- **`query`**: Loads targeted domain cards in **<2,000 tokens** before any code is touched.
- **`update`**: Incrementally synchronizes file checksums on mutation so knowledge never goes stale.

```bash
# Bootstrap repository knowledge
python ~/.claude/skills/gravitas/scripts/knowledge.py init

# Fast query for grounding agents or subagents
python ~/.claude/skills/gravitas/scripts/knowledge.py query "auth"

# Sync file checksums after code edits
python ~/.claude/skills/gravitas/scripts/knowledge.py update
```

---

## Install

```bash
npx gravitas-claude-code --yes
```

Or interactive (prompts before installing):

```bash
npx gravitas-claude-code
```

Restart Claude Code after install. The `/gravitas` skill becomes available immediately.

---

## What gets installed

```
~/.claude/skills/gravitas/     <- /gravitas skill
  ├── SKILL.md                 <- Core runtime invariants & decision records
  ├── PROMPT-TEMPLATE.md       <- 4-layer context assembly
  ├── agents/                  <- explore, plan, general, verify roles
  ├── references/              <- task contract, verification, delegation playbooks
  ├── resources/               <- knowledge-engine, claude-native, anti-rationalization
  └── scripts/                 <- knowledge.py, verify.py, detect_project.py
~/.claude/hooks/gravitas/      <- pre_tool.py, post_tool.py, stop_gate.py
~/.claude/settings.json        <- PreToolUse, PostToolUse, Stop hooks wired
```

---

## Evidence log

Per-session evidence is written to `.gravitas/sessions/<session-id>/`:

```
evidence.jsonl   -- reads, writes, test verdicts
failures.jsonl   -- tool failures with fingerprints
```

---

## Credit

Ported from [udaysharmadev/Gravitas](https://github.com/udaysharmadev/Gravitas) -- the original Antigravity runtime.  
Claude Code adaptation by [iiDOR](https://github.com/iiDOR).

## License

MIT
