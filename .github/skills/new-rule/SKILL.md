---
name: new-rule
description: Add a quality rule for batch files to plant_ops/rules.py, with its test and its row in docs/rules.md. Use when asked to add, write or create a batch file rule.
---

# Add a batch file rule

Input: the rule in plain English, for example "RunHours is greater than 0 and at most 12".

1. Work out by hand how many batches in `data/batch_2026-10-01.csv` break the rule: read the file, don't run new code to find out. Say the number and how you got it.
2. Add a row to the table in `docs/rules.md`: the next number, the rule's name, when a batch breaks it, and the count from step 1.
3. Add the rule to the dict that `check()` returns in `plant_ops/rules.py`, after the last rule, under the same name. It returns the batches that break it.
4. In `tests/test_rules.py`, add the name and the count to `EXPECTED`, last. Then add a test named `test_<short name>_catches_a_breaking_batch`: make one breaking batch from `batches[0]` with `dataclasses.replace`, and assert that the rule returns exactly that batch.
5. Run `pytest -q` and `ruff check .`, and report what passed.

Never change an existing rule, test or row.
