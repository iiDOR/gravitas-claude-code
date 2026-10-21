# Gravitas -- Delegation Reference (Claude Code Edition)

## Default: Single Agent

The default is a single capable agent. Delegation has overhead: context serialization,
token consumption, and coordination delay. Delegate only when the policy record says so.

## Four Conditional Subagent Roles

### 1. Investigator (Explore)
- **Prompt:** `agents/explore.md`
- **Spawn when:** Uncertainty is high, codebase is unfamiliar, or solution space is ambiguous.
- **Tools allowed:** `View`, `Grep`, `Glob`, `LS` (Strictly read-only).
- **Task:** Map relevant modules, callers, tests, and configurations. Never edit code.

### 2. Planner (Plan)
- **Prompt:** `agents/plan.md`
- **Spawn when:** High-risk implementation, architectural refactoring, or multi-step feature.
- **Tools allowed:** `View`, `Grep`, `Glob`.
- **Task:** Formulate implementation plan, pre-mortem, threat model, and acceptance criteria. Never edit code.

### 3. Implementer (General)
- **Prompt:** `agents/general.md`
- **Spawn when:** Executing the agreed plan in scoped steps.
- **Tools allowed:** `View`, `Edit`, `Replace`, `Write`, `Bash`.
- **Task:** Implement step-by-step, verify each step immediately, log failures to `SESSION_FAILURES.md`.

### 4. Verifier (Verify)
- **Prompt:** `agents/verify.md`
- **Spawn when:** Risk is medium/high, implementation is complete, or acceptance criteria are complex.
- **Tools allowed:** `View`, `Bash`, `Grep`.
- **Task:** Adversarial testing, test execution, regression auditing. Emits `VERDICT: PASS` or `VERDICT: FAIL`.

---

## How to Delegate in Claude Code

In Claude Code, subagents are invoked via the `Agent` or `Task` tool. When dispatching:
1. Provide the exact role prompt (`explore.md`, `plan.md`, `verify.md`).
2. Provide the `<task_contract>` and allowed file paths.
3. Provide known failures from `SESSION_FAILURES.md`.
4. Restrict subagent tool permissions to match the mode.
