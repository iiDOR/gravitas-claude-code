# Gravitas Living Knowledge Engine (GKE) -- Protocol & Playbook

> **The Gravitas Invariant 0:** Ground in Knowledge First, Synchronize on Mutation.
> Never initiate blind reconnaissance across dozens of files. Ground yourself in the
> persistent Knowledge Base first (<2,000 tokens), perform scoped surgery, and synchronize
> the knowledge base before concluding your turn.

---

## 1. THE PROBLEM: BLIND RECONNAISSANCE & CONTEXT EXHAUSTION

Standard coding agents suffer from a fundamental inefficiency pattern: **Reconnaissance Amnesia**.

```
[User Request]
       │
       ▼
[Blind Search: Grep/Glob across 50 files] ──► Consumes 40,000 - 80,000 tokens
       │
       ▼
[Context Bloat & Attention Dispersion]   ──► Model loses focus on core constraints
       │
       ▼
[Implementation & Partial Verification]
       │
       ▼
[Session End]                            ──► All discovered knowledge is lost!
       │
       ▼
[Next Turn / Subagent]                   ──► Starts from zero again! (Repeats 50k token grep)
```

In long sessions (10-25 turns), repetitive exploration eats over 500,000 tokens of input, inflates prompt costs by 80-90%, and degrades model reasoning due to needle-in-a-haystack attention fatigue.

### The Gravitas Living Knowledge Solution

Gravitas introduces a persistent, versioned, machine-readable knowledge substrate located at `.gravitas/knowledge/`. Instead of reading 50 source files, an agent consumes **1 or 2 targeted Knowledge Cards (1,500 - 3,000 tokens total)**, identifying exact entry points, threading constraints, and verification commands immediately.

---

## 2. THE 4-LAYER MEMORY ARCHITECTURE

Gravitas structures context into four strictly stratified layers:

```
┌────────────────────────────────────────────────────────┐
│ Layer 4: Context Delta & Active Slices                 │
│ (Active file lines, exact diffs, command stdout)      │
├────────────────────────────────────────────────────────┤
│ Layer 3: Ephemeral Task Contract & Failures            │
│ (<task_contract>, SESSION_FAILURES.md, decision logs)  │
├────────────────────────────────────────────────────────┤
│ Layer 2: Persistent Repository Knowledge Base (GKE)    │
│ (.gravitas/knowledge/: architecture, conventions, cards│
├────────────────────────────────────────────────────────┤
│ Layer 1: System Rules & Skill Invariants               │
│ (SKILL.md, prompt template, Claude Code toolchain)     │
└────────────────────────────────────────────────────────┘
```

- **Layer 1 (System Invariants)**: Non-negotiable behavioral boundaries (verification hierarchy, scope enforcement).
- **Layer 2 (Persistent Repository Knowledge)**: The living, self-updating map of the codebase. Survives session resets, compaction, and subagent boundaries.
- **Layer 3 (Task Contract & Session Memory)**: Scoped goals, allowed write paths, acceptance criteria, and failure recovery logs for the current task.
- **Layer 4 (Working Delta)**: Line-level file slices (`View`), exact git diffs, and compiler outputs. Discarded or summarized during compaction.

---

## 3. KNOWLEDGE BASE STRUCTURE (`.gravitas/knowledge/`)

The repository knowledge base resides in `.gravitas/knowledge/` and consists of deterministic markdown cards and a lightweight index:

```
.gravitas/
└── knowledge/
    ├── index.json             # Fast metadata catalog (IDs, tags, summaries, file hashes)
    ├── architecture.md        # System topology, module hierarchy, entry points
    ├── conventions.md         # Strict coding standards, error handling, threading rules
    ├── test-matrix.md         # Verification commands, linter commands, baseline test counts
    └── modules/               # Domain-specific deep dive cards
        ├── auth.md            # Authentication subsystem details
        ├── storage.md         # Database/persistence layer invariants
        └── scanner.md         # Domain engine cards
```

### Knowledge Card Schemas

#### A. `architecture.md` (System Topology)
- **Subsystems**: List of top-level directories and their single-sentence responsibilities.
- **Entry Points**: Canonical startup files, CLI drivers, or API route registries.
- **Data Flow & Boundaries**: High-level flow of state (e.g., Client -> Middleware -> Handler -> Service -> DB).
- **External Dependencies**: Critical third-party libraries, native bindings, or microservices.

#### B. `conventions.md` (Invariants & Rules)
- **Idiomatic Patterns**: Return types (e.g. `Result<T, E>` vs exceptions), async conventions.
- **Concurrency & Locking**: Mutex boundaries, thread affinity, deadlock prevention rules.
- **Antipatterns**: Explicitly forbidden practices (e.g., "Never modify global state without `g_HookMutex`", "No raw unparameterized SQL").

#### C. `test-matrix.md` (Verification Harness)
- **Deterministic Commands**: Exact CLI invocations for unit, integration, and smoke tests.
- **Linters & Type Checkers**: Exact flags (e.g. `tsc --noEmit`, `cargo clippy -- -D warnings`).
- **Baseline Pass Counts**: Expected test pass numbers before any edits (e.g. "42 passed, 0 failed").

#### D. Domain Module Cards (`modules/<id>.md`)
- Scoped domain cards created via `python scripts/knowledge.py add-card --id <id> --title <title>`.
- Contains internal interfaces, state structures, and module-specific invariants.

---

## 4. THE 3-PHASE CONTINUOUS KNOWLEDGE LIFECYCLE

```
  [1. INGEST / BOOTSTRAP]
            │
            ▼
  [2. GROUNDED EXECUTION] ◄────────┐
            │                      │ (Repeat)
            ▼                      │
  [3. DELTA SYNCHRONIZATION] ──────┘
```

### Phase 1: Ingest & Bootstrap (`scripts/knowledge.py init`)
Run when a repository is first entered or lacks `.gravitas/knowledge/`:
1. Execute `python scripts/knowledge.py init`.
2. GKE automatically detects languages (Rust, Go, TypeScript, Python, C/C++), build harnesses, and entry points.
3. Generates baseline templates for `architecture.md`, `conventions.md`, and `test-matrix.md`.
4. Computes SHA256 hashes of all source files to establish a baseline in `index.json`.

### Phase 2: Grounded Execution (`scripts/knowledge.py query`)
Before touching source files or launching subagents:
1. Query the knowledge base:
   ```bash
   python scripts/knowledge.py query "auth session"
   ```
   Or dump prompt-ready context:
   ```bash
   python scripts/knowledge.py query --format prompt
   ```
2. Read the identified cards. In 1,500 tokens, the agent knows:
   - Which file holds the target logic.
   - What invariants govern modification.
   - What command verifies the result.
3. Spawn an implementer or edit directly—**bypassing 90% of traditional grep exploratory steps**.

### Phase 3: Delta Synchronization (`scripts/knowledge.py update`)
Whenever code is mutated and verified (Phase 6: Deliver):
1. Execute:
   ```bash
   python scripts/knowledge.py update
   ```
2. GKE checks `git diff --name-only HEAD`, updates file tracking checksums in `index.json`, and highlights touched subsystems.
3. **Card Enrichment**: If the agent introduced a new export, refactored a pattern, or added a new test suite, it updates the corresponding markdown card (`architecture.md`, `conventions.md`, or `modules/<id>.md`) as part of its final delivery.
4. Verify synchronization status:
   ```bash
   python scripts/knowledge.py status --check
   ```
   (Returns exit code 0 if fully synced, 1 if unindexed changes remain).

---

## 5. INTEGRATION WITH SUBAGENTS (`Task` / `Agent`)

When spawning subagents in Claude Code:
1. **Never pass raw whole-codebase instructions.** Subagents will blindly grep and exhaust their subagent token budget.
2. **Inject Knowledge Cards directly:**
   ```markdown
   Task: "Implement token renewal logic in src/auth/token.ts."
   Context:
   <knowledge_context>
   [Output from `python scripts/knowledge.py query "auth"`]
   </knowledge_context>
   ```
3. The subagent starts already grounded in repository architecture and coding conventions.
4. Upon return, the coordinator reviews changes and runs `python scripts/knowledge.py update`.

---

## 6. QUANTIFIED TOKEN IMPACT

| Activity | Without GKE (Traditional) | With Gravitas GKE | Token Savings |
|----------|:-------------------------:|:-----------------:|:-------------:|
| Initial Reconnaissance | 35,000 - 80,000 tokens | 1,500 - 3,500 tokens | **~95% reduction** |
| Subagent Spawning Context | 20,000 - 45,000 tokens | 2,000 - 4,000 tokens | **~90% reduction** |
| Post-Compaction Resumption | 15,000 - 30,000 tokens | 2,500 tokens (query) | **~85% reduction** |
| Full Engineering Session (15 turns) | 450,000+ tokens | 95,000 tokens | **~78% total reduction** |

By transforming exploratory searches into structured, indexed lookups, Gravitas delivers the "10x context efficiency" necessary for high-speed, cost-effective, hallucination-free autonomous engineering.
