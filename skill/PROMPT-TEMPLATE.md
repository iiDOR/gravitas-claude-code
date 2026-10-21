# GRAVITAS Prompt Template (Claude Code Edition)

4-layer prompt assembly for optimal Claude Code performance and 10x token efficiency.
Every GRAVITAS task follows this structured context hierarchy.

---

## The 4-Layer System

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: System (static, load once, cacheable)          │
│  SKILL.md + references loaded only when needed           │
│  -> Core protocol, invariants, mode constraints         │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Persistent Repository Knowledge Base (GKE)    │
│  .gravitas/knowledge/ (architecture, conventions, cards)│
│  -> Persistent domain grounding, 90% recon token saving │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Task Contract (per-task, specific)             │
│  Goal, scope, constraints, acceptance criteria, output   │
│  -> What to do, where, and how to verify it             │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Context Delta (session/subagents/resumption)   │
│  Memory, active file slices, SESSION_FAILURES.md         │
│  -> What was learned, what failed, current diffs        │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: System Prompt (SKILL.md)

Load once. Cacheable. Contains the full GRAVITAS protocol.

**Contents:**
- Core Invariants (0-6)
- Policy record schema
- Extended thinking & reasoning calibration
- Compact recovery state
- Conditional delegation
- Output format & verification hierarchy

**When to load:** At session start. Once per session.

---

## Layer 2: Persistent Repository Knowledge Base

Stored in `.gravitas/knowledge/`. Managed via `python scripts/knowledge.py`.

Before any multi-file search, query the knowledge base to load high-density domain context:
```bash
python scripts/knowledge.py query "[domain keyword]"
```
Or generate compact XML for prompt injection:
```bash
python scripts/knowledge.py query --format prompt
```

This grounds the agent in architecture, conventions, and test commands in <2,000 tokens instead of wasting 40,000+ tokens on blind grep/read cycles.

---

## Layer 3: Task Prompt

Constructed fresh for each task. Maximum specificity using XML containers.

### Template

```xml
<task_contract>
  <mode>implement</mode>
  <objective>[One sentence: exactly what to accomplish]</objective>
  <scope>
    <target>[exact path or glob]</target>
    <related>[files that need reading or may be affected]</related>
    <tests>[test file path]</tests>
  </scope>
  <constraints>
    <constraint>[what NOT to do -- specific]</constraint>
    <constraint>[what to keep unchanged]</constraint>
    <constraint>[scope limit: "only touch files in src/auth/"]</constraint>
  </constraints>
  <acceptance_criteria>
    <criterion id="AC-1">[verifiable outcome 1]</criterion>
    <criterion id="AC-2">[verifiable outcome 2]</criterion>
  </acceptance_criteria>
  <verification_depth>impact</verification_depth>
</task_contract>
```

### Example: Bug Fix Task

```xml
<task_contract>
  <mode>implement</mode>
  <objective>Fix SESSION_TIMEOUT: change from 5,000ms to 30,000ms</objective>
  <scope>
    <target>src/auth/session.ts</target>
    <tests>src/auth/session.test.ts</tests>
  </scope>
  <constraints>
    <constraint>Only touch src/auth/session.ts and src/auth/session.test.ts</constraint>
    <constraint>Do not refactor the session module</constraint>
    <constraint>Do not modify other timeout constants in the module</constraint>
  </constraints>
  <acceptance_criteria>
    <criterion id="AC-1">SESSION_TIMEOUT constant set to 30000</criterion>
    <criterion id="AC-2">session.test.ts updated to assert 30000 and passes</criterion>
    <criterion id="AC-3">All other auth tests pass without regression</criterion>
  </acceptance_criteria>
  <verification_depth>impact</verification_depth>
</task_contract>
```

---

## Layer 4: Context Delta (for resumption and optional subagents)

Minimal context injected at spawn time or after context compression.

### For a Subagent Dispatch (via Agent / Task)

```xml
<subagent_context role="general">
  <knowledge_context>
    <card id="auth" title="Authentication Subsystem">
      Session tokens handled in src/auth/session.ts. Mutex lock required around store mutations.
    </card>
  </knowledge_context>
  <memory>
    <finding>SESSION_TIMEOUT at src/auth/session.ts:23 (confirmed via View)</finding>
    <finding>Test at session.test.ts:47 asserts 5000</finding>
  </memory>
  <session_failures>
    <failure>Tried editing config.ts -- wrong file, SESSION_TIMEOUT not there. Do NOT touch config.ts</failure>
  </session_failures>
  <baseline>47/47 tests pass before this change</baseline>
  <task_state>Explore complete. Implement lines 23 and 47 now.</task_state>
</subagent_context>
```

### For Long Sessions (after context compaction)

```markdown
## Session Summary -- [timestamp]

### Knowledge Base Grounding
- Subsystem: auth (card: .gravitas/knowledge/modules/auth.md)
- Invariants: Mutex lock around session map

### What We Have Established
- Bug: SESSION_TIMEOUT is 5,000 but should be 30,000
- Location: src/auth/session.ts:23
- Test impact: session.test.ts:47 asserts old value
- Scope confirmed: only 2 files need changing

### Session Failures
- config.ts was a dead end -- do not retry

### Status
General agent implementing now. Verify pending.
```

---

## Quick Templates by Task Type

### Bug Fix
```
Goal: Fix [symptom] -- [suspected cause]
Knowledge: python scripts/knowledge.py query "[domain]"
Files: [target] + [test]
Constraint: Stay in these files
Output: What Changed + Evidence + Knowledge Sync + VERDICT
Tier: balanced (compact)
```

### Feature Addition
```
Goal: Add [feature] to [module]
Knowledge: python scripts/knowledge.py query "[subsystem]"
Files: [implementation files] + [test files]
Constraint: [scope limits]
Output: Full ## sections + Knowledge Sync + VERDICT
Tier: balanced or deep depending on auth/security involvement
```

### Refactor
```
Goal: Refactor [what] to [why]
Knowledge: Check architecture.md & conventions.md
Files: [all affected files -- be exhaustive]
Constraint: No behavior changes, tests must pass unchanged
Output: What Changed + Evidence (before/after pass counts) + Knowledge Sync + VERDICT
Tier: deep if production module, compact otherwise
```

### Security Fix
```
Goal: Fix [vulnerability] in [location]
Knowledge: Check conventions.md for security invariants
Files: [target] + [tests] + [related modules]
Constraint: Don't introduce new endpoints. Don't change auth logic except the fix.
Output: Threat model + Fix + Security tests + Knowledge Sync + VERDICT
Tier: deep always
```
