# Model-Native Optimization Notes (Claude & Claude Code Tuned)

These patterns are tuned specifically for Anthropic Claude models (Claude 3.7 Sonnet,
Claude 4.5/4.6 Sonnet, Claude Opus 4.8, Claude Haiku 4.5) running inside **Claude Code**
or via the Anthropic API. They adapt the GRAVITAS reliability runtime to Claude's
distinct cognitive architecture, tool interfaces, and extended thinking mechanisms.

---

## 1. Extended Thinking & Adaptive Reasoning Calibration

Claude models feature native Extended Thinking (reasoning tokens before tool calls
and output). Match reasoning depth to expected error cost, reversibility, and blast radius.

| Task Tier / Mode | Extended Thinking Level | Token Budget | Rationale |
|---|:---:|:---:|---|
| **Direct / Eco** (single-file, obvious, reversible) | Low | ~1,000 - 2,000 | Brief sanity check, immediate tool execution |
| **Compact / Balanced** (dependent changes, multi-file) | Medium / High | ~4,000 - 8,000 | Trace dependencies, evaluate failure modes |
| **Deep** (architecture, security, migration) | Maximum | ~16,000 - 32,000 | Pre-mortem, threat model, rollback planning |
| **Replan / Recovery** (after a failed attempt) | High / Maximum | ~8,000 - 16,000 | Deep root-cause diagnosis; identify invalid assumptions |

### Thinking Rules for Claude
- **Reason inside `<thinking>` about failure modes, not self-praise.** Do not use thinking
  time to narrate how thorough you are. Use it to find edge cases, unhandled nulls, race conditions,
  and missing test assertions.
- **Never emit hidden chain-of-thought in user-visible blocks.** Machine-readable records
  (`<policy_record>`, `<decision_record>`) belong in structured outputs or tool inputs; internal
  deliberation stays inside the thinking process.
- **Circuit Breaker on Thinking Loops:** If thinking concludes that an approach has failed
  twice, stop immediately and trigger an explicit replan or query the user.

---

## 2. XML Tag Structural Isolation (Claude's Strongest Lever)

While Gemini prefers pure Markdown headings, **Claude excels at XML tag boundary parsing**.
Use XML tags to isolate contracts, decision records, evidence, and tool parameters from narrative text.

### Mandatory Machine-Checked Blocks

```xml
<task_contract>
  <mode>implement</mode>
  <objective>Add cursor pagination to /posts endpoint</objective>
  <acceptance_criteria>
    <criterion id="AC-1">Supports cursor parameter (opaque base64 string)</criterion>
    <criterion id="AC-2">Preserves existing response shape when cursor is omitted</criterion>
    <criterion id="AC-3">Returns 400 on malformed or expired cursor</criterion>
    <criterion id="AC-4">All existing post tests pass without regression</criterion>
  </acceptance_criteria>
  <allowed_write_scope>
    <path>src/routes/posts.ts</path>
    <path>tests/posts.test.ts</path>
  </allowed_write_scope>
  <verification_depth>impact</verification_depth>
</task_contract>
```

```xml
<policy_record>
{
  "planning": "compact",
  "context_depth": "dependency",
  "verification_depth": "impact",
  "delegation": "none",
  "reason_codes": ["multiple-files", "shared-route"]
}
</policy_record>
```

```xml
<decision_record>
  <action>Edit src/routes/posts.ts</action>
  <reason>Cursor parsing logic missing default fallback</reason>
  <evidence>
    <item>Read src/routes/posts.ts line 42: cursor parsed without validation</item>
    <item>Observed failing test: tests/posts.test.ts:88 expects 400 on invalid cursor</item>
  </evidence>
  <risk>low</risk>
  <allowed_by_contract>true</allowed_by_contract>
</decision_record>
```

---

## 3. Claude Code Toolset Mapping

Claude Code provides specialized tools that differ from Antigravity/Gemini.
Map GRAVITAS invariants to Claude Code native tools as follows:

| GRAVITAS Invariant | Claude Code Tool Mapping | Execution Rule |
|---|---|---|
| **1. Ground before mutating** | `View`, `Grep`, `Glob`, `LS` | Always call `View` on target lines before calling `Edit` or `Replace`. Never edit from assumed state. |
| **2. Stay in declared scope** | `Edit`, `Replace`, `Write` | Path must match `<allowed_write_scope>`. Writes outside scope violate Invariant 2. |
| **3. Completion needs evidence** | `Bash` | Execute test runners, type-checkers, and linters via `Bash`. Capture verbatim exit code and counts. |
| **4. Never exact-retry** | `View` `SESSION_FAILURES.md` | Read failure logs before retrying. Check approach against past dead ends. |
| **5. Satisfy the contract** | `Bash` (validators) | Check off each `<criterion>` with a fresh passing command output. |
| **6. Say what you can't verify** | User response / Verdict | Explicitly downgrade to `VERDICT: FAIL` or `VERDICT: UNVERIFIABLE` if tests cannot run. |

### Parallel Tool Calling in Claude Code
Claude Code can execute independent read tools concurrently. Always batch non-dependent queries:

```python
# GOOD — Parallel batch in single turn
[View(path="src/auth.ts")] + [View(path="tests/auth.test.ts")] + [Grep(pattern="SESSION_TIMEOUT")]

# BAD — Sequential round-trips
[View(path="src/auth.ts")]
# wait...
[View(path="tests/auth.test.ts")]
# wait...
[Grep(pattern="SESSION_TIMEOUT")]
```

---

## 4. Countering Claude-Specific Failure Modes

Claude models have specific behavioral tendencies that GRAVITAS actively counteracts:

### A. The "Sycophancy & False Confirmation" Trap
- **Tendency:** Claude wants to be agreeable and helpful, often saying "Everything looks correct!" or
  "The implementation is complete and verified" without executing tests.
- **Countermeasure (Invariant 3):** Prompt compliance and verbal assertions have zero weight.
  Completion is strictly gated on observed `Bash` command output with exit code `0` and verified pass counts.

### B. The Rationalization Trap
- **Tendency:** When a test fails or is missing, Claude often rationalizes:
  *"This test failure is likely due to pre-existing environmental issues, so our fix is good."*
- **Countermeasure:** See `resources/anti-rationalization.md`. An unexecuted test does not exist.
  A failing test is a failing verdict (`VERDICT: FAIL`). No exceptions.

### C. The Over-Apologetic Regression Loop
- **Tendency:** When corrected, Claude may enter a cycle of submissive apologies and try minor, random
  variations of the same broken code.
- **Countermeasure (Invariant 4):** State what actually happened. Never apologize excessively.
  Diagnose the root cause, record the failure in `SESSION_FAILURES.md`, change the strategy materially,
  and re-verify.

### D. File-Content Hallucination
- **Tendency:** Claude may recall a file from training or a previous turn and attempt an `Edit` on lines
  that have shifted or do not exist.
- **Countermeasure (Invariant 1):** Always call `View` on the specific line range before calling `Edit` or `Replace`.

---

## 5. Claude Code Context Compaction & Interruption Recovery

In Claude Code, long conversations undergo automatic context compaction or summarization.
Without persistent memory, compacted sessions suffer from amnesia, re-reading files, and repeating
failed approaches.

### Durable State Protocol
Maintain minimal state files on disk:
- `.gravitas/sessions/<task-id>/contract.json`: Task contract and scope boundaries.
- `.gravitas/sessions/<task-id>/state.json`: Current phase, completed criteria, and pending actions.
- `.gravitas/sessions/<task-id>/evidence.jsonl`: Append-only log of verified claims.
- `SESSION_FAILURES.md`: Human-readable log of failed approaches.

### Resumption Behavior
When Claude Code compacts the context:
1. Immediately check for `.gravitas/sessions/` and `SESSION_FAILURES.md`.
2. Do NOT re-read files marked as completed in `state.json`.
3. Do NOT retry approaches recorded in `SESSION_FAILURES.md`.
4. Resume execution directly from `next_action`.

---

## 6. Subagent Dispatching in Claude Code

When subagents are required, spawn them using Claude Code's `Agent` or `Task` tool:

| Role | Subagent Prompt Template | Allowed Tools | Goal |
|---|---|:---:|---|
| **Investigator (Explore)** | `agents/explore.md` | `View`, `Grep`, `Glob`, `LS` | Pure read-only recon; map dependencies, tests, configs. |
| **Planner (Plan)** | `agents/plan.md` | `View`, `Grep`, `Glob` | Adversarial design, pre-mortem, zero edits. |
| **Implementer (General)**| `agents/general.md` | `View`, `Edit`, `Replace`, `Write`, `Bash` | Scoped mutation, step-by-step verification. |
| **Verifier (Verify)** | `agents/verify.md` | `View`, `Bash`, `Grep` | Adversarial validation, test runs, strictly outputs `VERDICT: PASS/FAIL`. |

Always supply subagents with minimal necessary context (`<task_contract>`, target files, failure log)
and enforce read-only toolsets for recon and verification roles.
