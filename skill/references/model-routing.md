# Gravitas -- Model Routing Reference

> WARNING: This document describes a conceptual routing policy.
> The specific model ordering has NOT been benchmarked.
> Do not treat these recommendations as optimal until benchmark data confirms them.

## The Principle

Spend intelligence where expected error cost exceeds expected inference cost. Route to stronger models (or deeper effort) when the cost of getting it wrong exceeds the cost of a longer, more expensive run.

## Conceptual Routing Policy

```
simple fix / answer / review
  -> fast inexpensive model + eco

moderate feature / debugging
  -> fast inexpensive model + balanced

high uncertainty / architecture / security
  -> fast model (high effort) OR Pro-class model + deep

parallelizable large project
  -> parallel subagents

unresolvable failure after circuit breaker
  -> manual model escalation / user input
```

## When Native Features Are Better

Do not replicate what the host already does well:

| Task type | Use Gravitas | Use host native |
|-----------|:---:|:---:|
| Reliability enforcement | yes | -- |
| Evidence tracking | yes | -- |
| Requirement coverage | yes | -- |
| Interruption recovery | yes | -- |
| Parallel large project | -- | native parallelism |
| Maximum reasoning depth | -- | extended thinking |
| Single-session complex task | yes | -- |

## Quota-Aware Routing

Monitor quota state before starting a long session.

If premium model quota is low:
1. Switch to a fast inexpensive model + Gravitas (the intended fallback)
2. Gravitas state.json allows continuation from any model switch point
3. The reliability difference should be reduced by Gravitas enforcement

This is Gravitas's core use case: when the premium quota is gone, the fallback with Gravitas should lose less reliability than the bare fallback model.
