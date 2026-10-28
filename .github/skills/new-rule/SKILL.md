---
name: new-rule
description: Add a quality rule for batch files: in plant_ops/rules.py, in the gate notebook's rules() cell, or both, with its tests and its row in docs/rules.md. Use when asked to add, write or create a batch file rule.
---

# Add a batch file rule

Input: the rule in plain English, for example "RunHours is greater than 0 and at most 12", and where it goes: the app (`plant_ops/rules.py`), the gate notebook, or both. If it doesn't say, ask.

1. Work out by hand how many batches in `data/batch_2026-10-01.csv` break the rule: read the file, don't run new code to find out. Say the number and how you got it.
2. Add a row to the table in `docs/rules.md`: the next number, the rule's name, when a batch breaks it, and the count from step 1. If the rule is in the notebook only, say so in the "breaks it when" column.
3. For the app: add the rule to the dict that `check()` returns in `plant_ops/rules.py`, after the last rule, under the same name; add the name and the count to `EXPECTED` in `tests/test_rules.py`, and a test `test_<short name>_catches_a_breaking_batch` that makes one breaking batch from `batches[0]` with `dataclasses.replace`.
4. For the notebook: add the rule to the dict that `rules(df)` returns in `fabric/NB_Lab3_Gate.Notebook/notebook-content.py`, after the last rule, under the same name, with a one-line comment above it. Change no other cell and no `# META` line. The count test in `tests/fabric/test_gate_rules.py` picks it up from `docs/rules.md`; add a test `test_<short name>_catches_a_breaking_batch` there that changes one column with `make_batch(...)` and asserts the rule finds exactly one row.
5. Run `pytest -q` and `ruff check .`, and report what passed.

Never change an existing rule, test or row.
