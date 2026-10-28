"""Tests for the plant statistics.

PURPOSE  The rules a scrap rate must follow, checked on small, hand-made batches.
"""

from datetime import date, datetime

from plant_ops.batches import Batch
from plant_ops.stats import scrap_rate_by_plant

SEPTEMBER = (date(2026, 9, 1), date(2026, 9, 30))


def make(plant: str, day: date, produced: int, scrap: int) -> Batch:
    """A batch with only the fields the statistics read set to anything meaningful."""
    return Batch("T1", plant, "CH-CORR-01", "SKU001", day, datetime(day.year, day.month, day.day, 6), "A", 8.0, produced, scrap)


def test_rate_is_total_scrap_over_total_produced():
    batches = [make("P01", date(2026, 9, 10), 100, 10), make("P01", date(2026, 9, 11), 900, 0)]
    assert scrap_rate_by_plant(batches, *SEPTEMBER) == {"P01": 1.0}


def test_period_includes_both_end_days():
    batches = [make("P01", date(2026, 9, 1), 100, 1), make("P02", date(2026, 9, 30), 100, 2)]
    assert scrap_rate_by_plant(batches, *SEPTEMBER) == {"P01": 1.0, "P02": 2.0}


def test_batches_outside_the_period_are_ignored():
    batches = [make("P01", date(2026, 8, 31), 100, 50), make("P01", date(2026, 9, 15), 100, 5)]
    assert scrap_rate_by_plant(batches, *SEPTEMBER) == {"P01": 5.0}


def test_each_plant_is_reported_separately():
    batches = [make("P01", date(2026, 9, 15), 200, 2), make("P03", date(2026, 9, 15), 100, 3)]
    assert scrap_rate_by_plant(batches, *SEPTEMBER) == {"P01": 1.0, "P03": 3.0}
