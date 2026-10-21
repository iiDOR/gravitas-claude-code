# Gravitas -- Task Contract Reference (Claude Code Edition)

A task contract is a machine-readable declaration established at the start of any complex task.
It defines the mode, objective, acceptance criteria, scope boundaries, and budget profile.

## When to Use

Use a task contract when:
- The task has multiple acceptance criteria
- The allowed write scope should be constrained
- The task must run in a specific mode (plan-only, review, etc.)
- Interruption recovery or context compaction resilience is needed

## Schema

```xml
<task_contract>
  <mode>implement</mode>
  <objective>add cursor pagination to /posts endpoint</objective>
  <acceptance_criteria>
    <criterion id="AC-1">supports cursor parameter</criterion>
    <criterion id="AC-2">preserves existing response shape</criterion>
    <criterion id="AC-3">adds tests covering cursor and edge cases</criterion>
    <criterion id="AC-4">does not modify authentication</criterion>
  </acceptance_criteria>
  <non_goals>
    <item>do not add offset pagination</item>
  </non_goals>
  <risk>medium</risk>
  <budget>balanced</budget>
  <allowed_write_scope>
    <path>src/routes/posts.ts</path>
    <path>tests/posts.test.ts</path>
  </allowed_write_scope>
  <verification>targeted</verification>
</task_contract>
```

## Modes

| Mode | Allowed Writes | Use When |
|------|:--------------:|----------|
| answer | None | Pure question answering |
| research | None | Codebase exploration only |
| plan | None | Planning/design work, no implementation |
| review | None | Code review, no changes |
| debug | Limited | Diagnosis + targeted fix |
| implement | Scoped | Standard feature/fix work |
| migration | Confirmed | Schema/data migrations (destructive risk) |
| security-review | None | Security audit only |

Legacy aliases `plan-only` and `review-only` map to `plan` and `review`.

## Action Lock

In read-only modes (`answer`, `research`, `plan`, `review`, `security-review`), the runtime blocks
writes (`Edit`, `Replace`, `Write`) and non-query shell execution at tool level.
Prompt compliance is not relied upon: the model must refuse mutations while in read-only mode.

## Policy Dimensions

Beyond `risk` / `budget`, contracts declare explicit policy dimensions:
- `action_risk`: `low` | `medium` | `high` | `critical`
- `reversibility`: `full` | `partial` | `irreversible`
- `uncertainty`: `low` | `medium` | `high`
- `blast_radius`: `isolated` | `module` | `system`
- `verification_depth`: `smoke` | `targeted` | `impact` | `full`
- `reason_codes`: list of tags explaining the policy decision

Absent dimensions are treated as unknown, never as safe.

## Acceptance Criteria

Each criterion maps to a required evidence entry in the ledger.
Write criteria as verifiable outcomes, not process steps:
- GOOD: "returns 400 on invalid cursor"
- BAD: "handle edge cases appropriately"

## Allowed Write Scope

List specific files or directory prefixes. The agent must never touch files outside this scope.
If an edit is genuinely needed elsewhere, explicitly amend the contract first.

## Interruption Recovery

The contract is written to `.gravitas/sessions/<task-id>/contract.json` at task start.
If interrupted or compacted, the new context reads the contract and resumes from the evidence ledger state.
