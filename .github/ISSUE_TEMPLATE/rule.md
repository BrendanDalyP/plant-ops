---
name: Batch file rule
about: One new quality rule for batch files, sized for Copilot cloud agent
title: "Rule: "
labels: []
---

## Outcome

A batch file is rejected when one of its batches ...

## Acceptance tests

- [ ] A batch that breaks the rule (made with `dataclasses.replace` from a real one) is the only batch the rule returns.
- [ ] The rule returns no batches for `data/batch_2026-10-01.csv`.
- [ ] `pytest -q` and `ruff check .` pass.

## Files to touch

- `plant_ops/rules.py`
- `tests/test_rules.py`
- `docs/rules.md`

## How to verify

`pytest -q`

## Out of scope

Any other rule, the API, `.github/`.
