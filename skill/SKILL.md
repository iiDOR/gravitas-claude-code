---
name: gravitas
description: >
  Use for software implementation, debugging, refactoring, review, migration,
  and other repository-changing engineering work where correctness must be
  verified. Enforces scoped reconnaissance, adaptive planning, evidence-backed
  verification, requirement tracking, failure recovery, budget-aware
  delegation, and a persistent living knowledge base. Model-agnostic reliability
  runtime for coding agents -- measured, not claimed. Trigger this skill whenever
  the user asks you to implement a feature, fix a bug, refactor code, review changes,
  run a migration, or do any multi-step engineering task where "it should work" is
  not good enough -- use it even if the user doesn't say "gravitas" explicitly.
license: MIT
---

# GRAVITAS -- Engineering Reliability Runtime (Claude Code Edition)

**One rule above all:** Report what actually happened, not what you intended.
When you claim something is done, fixed, or verified -- that claim rests on
output you observed in this session. If you did not check, say you did not
check.

---

## THE CORE INVARIANTS

These hold across models and hosts. The runtime enforces the
machine-checkable ones at hook and tool level; the rest are on you.

0. **Ground in knowledge first, synchronize on mutation.** Consult `.gravitas/knowledge/`
   (`python scripts/knowledge.py query`) before blind grep/read across the repo. Ground your context
   in architecture, conventions, and test commands upfront (<2,000 tokens). Synchronize
   the knowledge base (`python scripts/knowledge.py update`) whenever code is mutated.
1. **Ground before mutating.** Read the target, its tests, and its callers
   before editing. Never act on assumed file state. Call `View` on exact lines first.
2. **Stay in declared scope.** Writes outside `allowed_write_scope` are
   denied. If the scope is wrong, amend the contract -- don't route around it.
3. **Completion needs evidence.** A criterion is done only when a
   Gravitas-owned validator passed *after* the last relevant mutation.
   Stale evidence, prompt assertions, and self-review don't count.
4. **Never exact-retry a failure.** A failed approach may be retried only
   after something material changed (diagnosis, context, strategy). Check
   `SESSION_FAILURES.md` before attempting a repair.
5. **Satisfy the contract.** Acceptance criteria and required validators in
   `contract.json` (or `<task_contract>`) gate completion. Generic "tests passed"
   doesn't cover unrelated criteria.
6. **Say what you can't verify.** Mark uncertain or unverifiable claims
   explicitly. Downgrade confidence instead of fabricating certainty.

---

## POLICY RECORD

Before multi-file or risky work, emit the planning-policy record (inside `<policy_record>`):

```json
{
  "planning": "compact",
  "context_depth": "dependency",
  "verification_depth": "impact",
  "delegation": "none",
  "reason_codes": ["multiple-files", "shared-module"]
}
```

- `planning`:
  - `direct`: trivial, localized fix in one file.
  - `compact`: dependent changes across 2-4 files, moderate uncertainty.
  - `deep`: architecture, security, schema migration, broad blast radius.
  - `replan`: evidence invalidated assumptions, scope grew, or repeated failure.
- `context_depth`: `minimal` | `targeted` | `dependency` | `full`.
- `verification_depth`: `smoke` | `targeted` | `impact` | `full`.
- `delegation`: `none` | `single` | `parallel`.

---

## MODES

| Mode | Allowed Tools | Meaning |
|------|:-------------:|---------|
| answer, research, plan, review, security-review | `View`, `Grep`, `Glob`, `LS` | Read-only. Deny edits and mutating shell commands. |
| implement, debug | `View`, `Edit`, `Replace`, `Write`, `Bash` | Normal work strictly inside `allowed_write_scope`. |
| migration | Confirmed | Destructive-risk work. User checkpoint required. |

See `references/task-contract.md`.

---

## DECISION RECORDS

For non-trivial actions, emit a decision record before mutating code:

```xml
<decision_record>
  <action>Edit src/auth/session.ts</action>
  <reason>SESSION_TIMEOUT is 5000ms, task requires 30000ms</reason>
  <evidence>
    <item>Read src/auth/session.ts line 23: SESSION_TIMEOUT = 5000</item>
    <item>Failing test: auth/session.test.ts:47 expects 5000 (needs update)</item>
  </evidence>
  <risk>low</risk>
  <allowed_by_contract>true</allowed_by_contract>
</decision_record>
```

---

## VERIFICATION HIERARCHY

Prefer executable evidence over prose, in this order:

1. Hidden deterministic acceptance validator (`python scripts/verify.py` or project test suite)
2. External integration / runtime execution
3. Project test runner (`vitest`, `pytest`, `cargo test`, `go test`, `ctest`)
4. Compiler / type checker (`tsc --noEmit`, `mypy`, `cargo check`)
5. Deterministic static analysis (`eslint`, `ruff`, `clippy`)
6. Executable reproducer script
7. Structural / diff / knowledge invariant (`python scripts/knowledge.py status --check`)
8. Independent model review
9. Same-model self-review (supplementary only -- never completion evidence)

Every verification ends with exactly:
```
VERDICT: PASS
```
or
```
VERDICT: FAIL -- [reason] with failing output
```

See `references/verification.md` for validator discovery and escalation
(`targeted` -> `impact` -> `suite` -> `full`).

---

## EFFORT PROFILES & EXTENDED THINKING

| Profile | Planning | Extended Thinking | Delegation | Verification |
|---------|----------|:-----------------:|------------|--------------|
| eco | direct-first | Low (~1k tokens) | none unless blocked | targeted only |
| balanced | adaptive (default) | Medium (~4-8k tokens) | conditional | targeted + affected |
| deep | deep-first | Maximum (~16-32k tokens) | conditional verifier | full suite + independent check |

See `resources/claude-native.md` for extended thinking calibration on Claude 3.7+ and 4+.

---

## DELEGATION & SUBAGENTS

Default to one capable agent. Delegate only when the policy record says so:

| Signal | Role | Claude Code Prompt |
|--------|------|-------------------|
| Localization uncertain, read-only | investigator | `agents/explore.md` |
| Complex implementation architecture | planner | `agents/plan.md` |
| Scoped mutation & step testing | implementer | `agents/general.md` |
| Adversarial verification | verifier | `agents/verify.md` |

Subagents receive minimal necessary context plus explicit tool permissions via Claude Code's `Agent` or `Task` tool. Always inject relevant knowledge cards (`python scripts/knowledge.py query --format prompt`) to prevent subagents from wasting tokens on redundant exploration.

---

## OUTPUT FORMAT

Every non-trivial engineering response must conclude with:

```markdown
## What Changed
[files modified, lines changed, behavior delta]

## Evidence
[verbatim command output -- pass counts, lint results, build output, exit codes]

## Knowledge Sync
[status of knowledge base: python scripts/knowledge.py status --check]

## Why
[rationale for the key architectural or code decision]

VERDICT: PASS
```

---

## RECON CHECKLIST (Before Any Mutation)

Run in parallel:
- Consult Knowledge Base: `python scripts/knowledge.py query "<keyword>"` or read `.gravitas/knowledge/`
- Read the target file -- exact lines needed (`View`)
- Read files it imports / that import it (`Grep`)
- Read the test file (`View`)
- Check repository conventions in `.gravitas/knowledge/conventions.md`
- `git log --oneline -5 -- [target]`
- `git diff HEAD -- [target]`

---

## DEEP REFERENCES

Load when the task requires:

| Reference | Load when |
|-----------|-----------|
| `references/task-contract.md` | establishing a formal task contract |
| `references/reasoning.md` | calibrating reasoning depth |
| `references/reconnaissance.md` | large/unfamiliar codebase recon |
| `references/verification.md` | complex verification requirements |
| `references/delegation.md` | considering subagent spawning |
| `references/recovery.md` | resuming after interruption or compaction |
| `references/model-routing.md` | budget/model selection decisions |

## RESOURCES

Deep playbooks:

| Resource | Load when |
|----------|-----------|
| `resources/knowledge-engine.md` | Living Knowledge Base (GKE), context reduction, persistent memory |
| `resources/claude-native.md` | Claude Code prompt structure, extended thinking & failure modes |
| `resources/adversarial-critique.md` | before implementing any plan (7 attack vectors) |
| `resources/anti-rationalization.md` | catching model shortcuts and rationalization |
| `resources/context-management.md` | long sessions, large codebases, subagent context |
| `resources/verification-engine.md` | full verification chains by language |
| `resources/subagent-patterns.md` | spawning/coordinating subagents in Claude Code |
| `resources/memory-protocol.md` | cross-session continuity, `SESSION_FAILURES.md` |
| `resources/tool-orchestration.md` | parallel tool batching, search patterns |

---

Read before write. Plan before act. Verify with proof. Report what happened.
