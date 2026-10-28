"""Production batches, as the plants report them.

PURPOSE  Turn a batch CSV (the plants' export format) into typed Batch objects. Every other
         module works with Batch objects, never with raw CSV rows.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class Batch:
    """One production batch: one machine, one SKU, one shift."""

    batch_id: str  # BatchId, e.g. "X00001"
    plant_id: str  # PlantId, e.g. "P01"
    asset_id: str  # AssetId: the machine, e.g. "CH-CORR-01"
    sku_id: str  # SkuId: the product made, e.g. "SKU223"
    shift_date: date  # ShiftDate, "YYYY-MM-DD"
    shift_start: datetime  # ShiftStart, "YYYY-MM-DD HH:MM:SS"
    shift: str  # Shift: "A", "B" or "C"
    run_hours: float  # RunHours, e.g. 2.78
    square_feet_produced: int  # SquareFeetProduced
    scrap_square_feet: int  # ScrapSquareFeet


def read_batches(path: str | Path) -> list[Batch]:
    """Read a batch CSV into Batch objects, in file order.

    PURPOSE     Batch files on disk: the history, and the files in data/.
    PSEUDOCODE  open the file; return parse_batches(its lines)
    """
    with open(path, newline="", encoding="utf-8") as f:
        return parse_batches(f)


def parse_batches(lines: Iterable[str]) -> list[Batch]:
    """Turn the lines of a batch CSV, header first, into Batch objects in order.

    PURPOSE     The same parsing for a file on disk and for an upload that only exists in memory.
    PSEUDOCODE  for each row from csv.DictReader(lines):
                    convert each column to its field's type; append a Batch
                a missing column raises KeyError; a bad number or date raises ValueError
    """
    batches = []
    for row in csv.DictReader(lines):
        batches.append(
            Batch(
                batch_id=row["BatchId"],
                plant_id=row["PlantId"],
                asset_id=row["AssetId"],
                sku_id=row["SkuId"],
                shift_date=date.fromisoformat(row["ShiftDate"]),
                shift_start=datetime.strptime(row["ShiftStart"], "%Y-%m-%d %H:%M:%S"),
                shift=row["Shift"],
                run_hours=float(row["RunHours"]),
                square_feet_produced=int(row["SquareFeetProduced"]),
                scrap_square_feet=int(row["ScrapSquareFeet"]),
            )
        )
    return batches
