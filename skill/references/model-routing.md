# Gravitas -- Model Routing Reference (Claude Family)

## The Principle

Use the least expensive model that can reliably accomplish the task under Gravitas runtime constraints.
Escalate model tier only when complexity, uncertainty, or blast radius requires it.

## Routing Policy for Claude Models

```
simple fix / documentation / localized edit / smoke test
  -> Claude Haiku 4.5 / 3.5 + eco profile

standard feature implementation / refactoring / bug diagnosis
  -> Claude Sonnet 4.6 / 3.7 + balanced profile (Extended Thinking: Medium)

architecture design / security audit / complex migration / tricky debug
  -> Claude Opus 4.8 / Claude Sonnet 4.6 + deep profile (Extended Thinking: Maximum)

circuit-breaker triggered after 2 failed attempts
  -> Escalate thinking budget to Maximum OR escalate to Opus
```

## Quota-Aware Graceful Degradation

If premium model quota is constrained:
1. Switch to Claude Sonnet or Haiku combined with GRAVITAS enforcement.
2. Gravitas `.gravitas/sessions/<task-id>/state.json` preserves state across model switches.
3. The deterministic verification gate (`python scripts/verify.py`) prevents quality degradation
   regardless of which model executes the prompt.
