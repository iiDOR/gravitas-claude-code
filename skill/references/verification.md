# Gravitas -- Verification Reference (Claude Code Edition)

## The Hierarchy

Prefer external, deterministic evidence over model self-assessment:
1. Deterministic acceptance validator (`python scripts/verify.py` or hidden harness)
2. Compiler / type checker (`tsc --noEmit`, `mypy --strict`, `cargo check`)
3. Unit test runner with actual terminal output (`vitest`, `pytest`, `cargo test`, `go test`)
4. Integration test runner
5. Static analysis (`eslint`, `ruff`, `cargo clippy`)
6. Executable reproducer script
7. Diff inspection
8. Independent model review
9. Model self-review (supplementary only, lowest weight -- never completion evidence)

Model self-critique is not verification. It is a weak signal to use only when no better evidence exists.

---

## Evidence Requirements by Claim

| Claim | Minimum Required Evidence |
|-------|--------------------------|
| Tests pass | Pass count + total + 0 failures from actual `Bash` run |
| Lint clean | Linter output with 0 warnings/errors |
| Type-safe | `tsc`/`mypy`/`pyright` output completely clean |
| Build succeeds | Exit code 0 + binary/artifact generated |
| No regressions | Before count vs after count, both shown verbatim |
| Fixed | Before behavior observed (failing), after behavior observed (passing) |
| Requirement covered | Evidence entry in ledger linking criterion to proof |

---

## VERDICT Format

Every verification session ends with exactly one of:

```
VERDICT: PASS
```
or
```
VERDICT: FAIL -- [specific reason]
[failing output]
```

Never: `VERDICT: PASS (with caveats)` -- that is a FAIL.
Never: `VERDICT: PARTIAL PASS` -- that is a FAIL.

---

## Regression Baseline

Before any mutation:
1. Run full test suite, record exact pass count.
2. Note existing lint warnings (do not introduce new ones).

After changes:
1. Run full test suite.
2. Ensure after count >= before count.
3. Fix any newly introduced lint warnings before emitting `VERDICT: PASS`.

---

## Scope-Appropriate Verification

Never run every validator blindly. Discover first, then escalate:

| Depth | Runs | When Applied |
|-------|------|--------------|
| `targeted` | Test validators scoped strictly to changed files | Always (baseline) |
| `impact` | Changed files + callers/importers + related tests | Multi-file changes, broad fanout |
| `suite` | Full project test suite | Shared utilities, core models, release context |
| `full` | Complete suite + linters + type-checker + CI workflows | Security, auth, schema migrations |

---

## Requirement-Evidence States

Each criterion in the task contract has one of these states:
- `PENDING`: Not yet verified
- `SUPPORTED`: Indirect or partial evidence (never gates completion alone)
- `PASS`: Fresh Gravitas-owned validator passed *after* last mutation
- `FAIL`: Validator ran and failed
- `BLOCKED`: Missing dependency or hardware environment
- `UNVERIFIABLE`: Stated limitation, requires human verification

Only fresh Gravitas-owned validator `PASS` gates completion. Evidence predating the final mutation is stale.

---

## Reproduction-First Debugging

```
symptom -> reproduce -> record failing evidence -> localize -> patch
        -> rerun SAME reproduction -> regression verification
```

1. **Confirm the bug with a reproducer:** Must FAIL before the fix.
2. **Patch:** Make minimal necessary mutation.
3. **Rerun reproducer:** Must PASS after the fix.
4. **Run regression tests:** Ensure unrelated tests remain green.

When reproduction is impossible, state why explicitly:
```
Reproduction blocked: requires production payment gateway credentials.
Marking AC-1 as UNVERIFIABLE. Confidence downgraded.
```

---

## Adversarial Edge Cases (Strict / Security Work)

For security, auth, algorithms, and stateful behavior:
- Boundary tests (0, -1, INT_MAX, empty strings, null, NaN, unicode overflows).
- Concurrency races and lock contention.
- Error path assertions (network timeouts, disk full, invalid tokens).

---

## Completion Gating

Completion is strictly blocked until:
- All acceptance criteria have evidence entries in the ledger.
- Required validators have been observed running in the current turn.
- No unresolved failures exist in `SESSION_FAILURES.md`.
- The output concludes with `VERDICT: PASS`.
