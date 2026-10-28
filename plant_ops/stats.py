"""Production statistics for the plant managers' reports.

PURPOSE  The numbers people ask for most, computed from Batch objects.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from plant_ops.batches import Batch


def scrap_rate_by_plant(batches: list[Batch], start: date, end: date) -> dict[str, float | None]:
    """Scrap rate per plant, as a percentage, for batches from start to end.

    PURPOSE     The number plant managers ask for: scrap square feet / square feet produced x 100.
    PSEUDOCODE  keep batches whose shift_date is from start to end, both days included
                group them by plant
                rate = total scrap square feet / total square feet produced x 100, rounded to 2 places
                a plant that produced nothing in the period gets None: its rate is unknown, not 0
    """
    produced: dict[str, int] = defaultdict(int)
    scrap: dict[str, int] = defaultdict(int)
    for b in batches:
        if start <= b.shift_date <= end:
            produced[b.plant_id] += b.square_feet_produced
            scrap[b.plant_id] += b.scrap_square_feet
    return {p: round(scrap[p] / produced[p] * 100, 2) if produced[p] else None for p in produced}


def square_feet_per_run_hour_by_plant(batches: list[Batch], start: date, end: date) -> dict[str, float | None]:
    """Square feet produced per run hour, per plant, for batches from start to end.

    PURPOSE     How much board each plant runs per hour of machine time: the data team's Square Feet per Run Hour.
    PSEUDOCODE  keep batches whose shift_date is from start to end, both days included
                group them by plant
                rate = total square feet produced / total run hours, rounded to 1 place
                a plant with no run hours in the period gets None: its rate is unknown, not 0
    """
    produced: dict[str, int] = defaultdict(int)
    hours: dict[str, float] = defaultdict(float)
    for b in batches:
        if start <= b.shift_date <= end:
            produced[b.plant_id] += b.square_feet_produced
            hours[b.plant_id] += b.run_hours
    return {p: round(produced[p] / hours[p], 1) if hours[p] else None for p in produced}
