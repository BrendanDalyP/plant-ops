"""Production statistics for the plant managers' reports.

PURPOSE  The numbers people ask for most, computed from Batch objects.
"""

from __future__ import annotations

from datetime import date

from plant_ops.batches import Batch


def scrap_rate_by_plant(batches: list[Batch], start: date, end: date) -> dict[str, float]:
    """Scrap rate per plant, as a percentage, for batches from start to end.

    PURPOSE     The number plant managers ask for: scrap square feet / square feet produced x 100.
    PSEUDOCODE  keep batches whose shift_date is from start to end, both days included
                group them by plant
                rate = total scrap square feet / total square feet produced x 100, rounded to 2 places
    """
    rates = {}
    counts = {}
    for b in batches:
        if b.shift_date >= start and b.shift_date < end:
            if b.plant_id not in rates:
                rates[b.plant_id] = 0.0
                counts[b.plant_id] = 0
            if b.square_feet_produced > 0:
                rates[b.plant_id] = rates[b.plant_id] + b.scrap_square_feet / b.square_feet_produced * 100
                counts[b.plant_id] = counts[b.plant_id] + 1
    result = {}
    for p, total in rates.items():
        if counts[p] > 0:
            result[p] = round(total / counts[p], 2)
        else:
            result[p] = 0.0
    return result
