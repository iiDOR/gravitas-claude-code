# Gravitas -- Reconnaissance Reference (Claude Code Edition)

## Recon Principle

Inspect enough context to reduce relevant uncertainty -- not the whole repository.
Recon scope is determined by the task's impact graph, not by default thoroughness.

## Standard Recon (Simple Tasks)

Run these in parallel:
- Read the target file (`View`)
- Find and read direct importers (`Grep` for module imports)
- Read the test file (`View`)
- Check recent changes: `git log --oneline -5 -- target`
- Check configuration: read `package.json`, `tsconfig.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod`

## Extended Recon (Unfamiliar Codebase or High Fan-Out)

Add:
- Architecture overview: `LS` src/, read `README.md`
- Pattern discovery: `Grep` similar patterns across codebase
- Full caller graph for changed symbol
- Related test suites

## Dependency-Directed Recon

For functions or APIs with high caller counts, recon must cover:
- Changed symbol
  -> direct callers (read all)
  -> public interface files (read all)
  -> test files for callers (read)
  -> config/schema if behavior changes

## Recon Completeness Check

Before moving to planning, confirm:
- I have called `View` on the target file (never assumed its content)
- I know which files import or call the target
- I know the test coverage for the target
- I know whether recent git changes are relevant
- I know the blast radius of the proposed change
