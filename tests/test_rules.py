"""Tests for batch quality rules."""

from dataclasses import replace

import pytest

from plant_ops.batches import read_batches
from plant_ops.reference_data import DATA
from plant_ops.rules import batches_with_invalid_run_hours

BATCH_FILE = DATA / "batch_2026-10-01.csv"


@pytest.mark.parametrize("run_hours", [-0.1, 0, 12.01])
def test_returns_only_batches_with_run_hours_outside_the_allowed_range(run_hours):
    batch = replace(read_batches(BATCH_FILE)[0], run_hours=run_hours)
    valid_batch = replace(batch, run_hours=12)

    assert batches_with_invalid_run_hours([valid_batch, batch]) == [batch]


@pytest.mark.parametrize("run_hours", [0.01, 12])
def test_run_hours_at_valid_boundaries_are_accepted(run_hours):
    batch = replace(read_batches(BATCH_FILE)[0], run_hours=run_hours)

    assert batches_with_invalid_run_hours([batch]) == []


def test_sample_batch_file_has_no_run_hours_violations():
    assert batches_with_invalid_run_hours(read_batches(BATCH_FILE)) == []
