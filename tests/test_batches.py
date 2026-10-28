"""Tests for reading batch files (Part 2 makes these pass).

PURPOSE  Pin down the CSV layout and every column's type before anything builds on read_batches.
"""

from datetime import date, datetime

from plant_ops.batches import Batch, read_batches
from plant_ops.reference_data import DATA

BATCH_FILE = DATA / "batch_2026-10-01.csv"


def test_reads_every_row():
    assert len(read_batches(BATCH_FILE)) == 53


def test_first_row_has_typed_values():
    assert read_batches(BATCH_FILE)[0] == Batch(
        "X00001", "P01", "CH-CORR-01", "SKU223", date(2026, 10, 1), datetime(2026, 10, 1, 14, 13), "B", 2.78, 284972, 12092
    )


def test_negative_numbers_are_kept():
    x00004 = next(b for b in read_batches(BATCH_FILE) if b.batch_id == "X00004")
    assert x00004.scrap_square_feet == -5479


def test_history_file_reads_too():
    assert len(read_batches(DATA / "production_history.csv")) == 1943
