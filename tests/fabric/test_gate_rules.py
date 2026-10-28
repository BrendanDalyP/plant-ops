"""Tests for the gate notebook's rules() cell, run on local Spark.

PURPOSE  The notebook must agree with Day 4: the same rules, the same names, and the counts in docs/rules.md
         for today's batch file. Expected counts are read from the doc, never from running the code.
PSEUDOCODE
  EXPECTED = {rule name: count} from the table in docs/rules.md (its last column)
  for each rule: the notebook has it, and it finds that many rows in data/batch_2026-10-01.csv
  48 batches break no rule
  edge cases copied from Day 4's tests: scrap above produced, run hours at 0, below 0, above 12 and exactly 12
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RULES_MD = (ROOT / "docs" / "rules.md").read_text(encoding="utf-8")
EXPECTED = {m.group(2).strip(): int(m.group(3))
            for m in re.finditer(r"^\| (\d+) \| ([^|]+) \|[^|]+\| (\d+) \|$", RULES_MD, re.MULTILINE)}
SCRAP = "Scrap is not more than produced"
HOURS = "RunHours is greater than 0 and at most 12"


@pytest.mark.parametrize("rule, count", EXPECTED.items())
def test_rule_count(results, rule, count):
    assert rule in results, f"the notebook's rules() has no rule named {rule!r} yet"
    assert results[rule] == count


def test_48_batches_break_no_rule(rules, staged):
    bad = None
    for rows in rules(staged).values():
        ids = rows.select("BatchId")
        bad = ids if bad is None else bad.union(ids)
    assert staged.join(bad.distinct(), "BatchId", "left_anti").count() == 48


def test_scrap_rule_catches_a_breaking_batch(rules, make_batch):
    batch = make_batch(ScrapSquareFeet=284973)          # X00001 produced 284,972 square feet
    assert rules(batch)[SCRAP].count() == 1


@pytest.mark.parametrize("hours", [0.0, -1.5, 12.01])
def test_run_hours_rule_catches_a_breaking_batch(rules, make_batch, hours):
    assert rules(make_batch(RunHours=hours))[HOURS].count() == 1


def test_run_hours_rule_allows_exactly_12(rules, make_batch):
    assert rules(make_batch(RunHours=12.0))[HOURS].count() == 0
