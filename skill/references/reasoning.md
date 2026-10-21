# Gravitas -- Adaptive Reasoning Reference (Claude Code Edition)

## The Core Principle

Reasoning depth must be proportional to expected error cost, reversibility, and blast radius.

Do not apply:
- Fixed token floors (e.g. forcing 10k tokens on trivial 1-line changes)
- Reasoning theater (narrating obvious facts without finding edge cases)
- Hallucinated chain-of-thought in user-visible blocks

Do apply:
- Deeper extended thinking when getting it wrong is destructive or hard to revert
- Brief extended thinking when the path forward is unambiguous and contained
- Explicit decision records when the choice affects architecture or public APIs

---

## Reasoning Depth Formula

```
reasoning_depth = base
  + risk_weight(risk_tier)
  + uncertainty_weight(requirement_clarity)
  + fan_out_weight(dependency_count)
  + failure_weight(prior_failed_attempts)
  + irreversibility_weight(can_this_be_undone)
  + deficit_weight(missing_evidence_for_decision)
```

## Calibration by Scenario in Claude Code

| Scenario | Extended Thinking Depth | Thinking Budget | Focus |
|---|:---:|:---:|---|
| Typo / localized bug fix | Low | ~1k - 2k tokens | Verify line number, check immediate callers |
| New utility function | Moderate | ~3k - 5k tokens | Edge cases (null, empty), type signatures |
| Multi-file feature | High | ~6k - 12k tokens | Data flow, caller contracts, regression risk |
| Auth, crypto, or security | Maximum | ~16k - 32k tokens | Threat model, bypass surface, replay attacks |
| Schema migration | Maximum | ~16k - 32k tokens | Backward compatibility, data loss, rollback |
| 2nd attempt after failure | High / Maximum | ~8k - 16k tokens | Root-cause post-mortem, why did attempt 1 fail |

---

## Selective Chain-of-Thought

Practical rules:
- Emit explicit reasoning inside `<thinking>` to deliberate on risks and invariants.
- Emit a `<decision_record>` before mutating non-trivial code.
- Keep final user-visible response structured and evidence-focused (`## What Changed`, `## Evidence`, `## Why`, `VERDICT`).
