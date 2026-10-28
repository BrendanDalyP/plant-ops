"""Tests for the batch file rules.

PURPOSE  Check every rule against the answer key in docs/rules.md. The expected counts are typed
         from the doc, never taken from running the code.
"""

from dataclasses import replace

import pytest

from plant_ops.batches import read_batches
from plant_ops.reference_data import DATA, load_asset_plants, load_sku_ids
from plant_ops.rules import check, failing_ids

EXPECTED = {  # docs/rules.md, last column
    "BatchId is present": 0,
    "BatchId is unique in the file": 2,
    "Square feet are not negative": 1,
    "SkuId exists": 1,
    "PlantId is the machine's plant": 1,
    "BatchId is not already loaded": 0,
}


@pytest.fixture(scope="module")
def batches():
    return read_batches(DATA / "batch_2026-10-01.csv")


@pytest.fixture(scope="module")
def results(batches):
    history = read_batches(DATA / "production_history.csv")
    return run_rules(batches, loaded_ids={b.batch_id for b in history})


def run_rules(batches, loaded_ids=frozenset()):
    return check(batches, sku_ids=load_sku_ids(), asset_plants=load_asset_plants(), loaded_ids=set(loaded_ids))


def test_every_rule_is_checked(results):
    assert list(results) == list(EXPECTED)


@pytest.mark.parametrize("rule, count", EXPECTED.items())
def test_rule_count(results, rule, count):
    assert len(results[rule]) == count


def test_48_batches_break_no_rule(batches, results):
    bad = failing_ids(results)
    assert sum(1 for b in batches if b.batch_id not in bad) == 48


def test_a_batch_already_loaded_breaks_rule_6(batches):
    results = run_rules(batches[:1], loaded_ids={batches[0].batch_id})
    assert results["BatchId is not already loaded"] == [batches[0]]


def test_a_batch_without_an_id_breaks_rule_1(batches):
    no_id = replace(batches[0], batch_id="")
    assert run_rules([no_id])["BatchId is present"] == [no_id]
