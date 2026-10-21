# Gravitas -- Interruption Recovery Reference (Claude Code Edition)

## The Problem

Long engineering sessions in Claude Code can be interrupted by context compaction,
model switches, or user ending and resuming a session. Without persistent state,
the new context re-reads files, re-plans, and retries failed approaches.

## The Solution

Gravitas maintains minimal durable state that survives context compaction.

## State File: `.gravitas/sessions/<task-id>/state.json`

```json
{
  "task_id": "add-cursor-pagination-2026-09-11",
  "contract": "./contract.json",
  "phase": "verify",
  "completed_criteria": ["AC-1", "AC-2"],
  "pending_criteria": ["AC-3"],
  "files_touched": ["src/routes/posts.ts", "tests/posts.test.ts"],
  "known_failures": [],
  "last_successful_action": "wrote cursor parameter handling in posts.ts",
  "next_action": "run cursor pagination test suite"
}
```

## Evidence Ledger: `.gravitas/sessions/<task-id>/evidence.jsonl`

Append-only log of completed verifications:
```jsonl
{"criterion": "AC-1", "evidence": "vitest run: 47 passed", "timestamp": "2026-09-11T02:30:00Z"}
{"criterion": "AC-2", "evidence": "diff: serializer.ts unchanged", "timestamp": "2026-09-11T02:31:00Z"}
```

## Failure Log: `SESSION_FAILURES.md`

```markdown
# Session Failures
- Approach: Direct timeout change in config.ts
  Reason: Test expects original value; constant is in session.ts
  Timestamp: 2026-09-11T02:28:00Z
```

## Recovery Protocol

When resuming after compaction or interruption:
1. Check for `.gravitas/sessions/` directory and `SESSION_FAILURES.md`.
2. Find the most recent session matching the task.
3. Read `state.json` -- determine current phase and pending criteria.
4. Read `evidence.jsonl` -- understand what has been verified.
5. Read `SESSION_FAILURES.md` -- do not retry listed approaches.
6. Resume directly from `next_action`.
7. Do NOT re-read files that `state.json` shows were already processed.

## Circuit Breaker

- Same failure x2: force root-cause diagnosis.
- Same strategy x2: force replan (approach does not work).
- Verification cycles >3: report blocked, request user intervention.
