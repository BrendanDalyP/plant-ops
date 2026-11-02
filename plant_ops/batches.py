"""Production batches, as the plants report them.

PURPOSE  Turn a batch CSV (the plants' export format) into typed Batch objects. Every other
         module works with Batch objects, never with raw CSV rows.
"""

from __future__ import annotations

import csv 
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

    PURPOSE     One place that knows the CSV layout and the type of every column.
    PSEUDOCODE  open the file; for each row from csv.DictReader:
                    convert each column to its field's type (date, datetime, float, int)
                    append a Batch
                return the list
    """
    batches = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batches.append(
                Batch(
                    batch_id=row["BatchId"],
                    plant_id=row["PlantId"],
                    asset_id=row["AssetId"],
                    sku_id=row["SkuId"],
                    shift_date=datetime.strptime(row["ShiftDate"], "%Y-%m-%d").date(),
                    shift_start=datetime.strptime(row["ShiftStart"], "%Y-%m-%d %H:%M:%S"),
                    shift=row["Shift"],
                    run_hours=float(row["RunHours"]),
                    square_feet_produced=int(row["SquareFeetProduced"]),
                    scrap_square_feet=int(row["ScrapSquareFeet"]),
                )
            )
    return batches

