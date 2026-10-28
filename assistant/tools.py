"""The assistant's tools: this app's numbers, for the model to ask for.

PURPOSE  Each tool wraps Day 4 code the tests already trust, and returns a dict the model reads. Its description and
         parameter descriptions are what the model sees when it chooses a tool, so they say what the tool does,
         the units, and the definition. Bad input comes back as {"error": ...} so the model can ask again.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from agent_framework import tool
from pydantic import Field

from plant_ops.batches import read_batches
from plant_ops.reference_data import DATA, load_asset_plants, load_sku_ids
from plant_ops.rules import check, failing_ids
from plant_ops.stats import scrap_rate_by_plant, square_feet_per_run_hour_by_plant
from plant_ops.store import BatchStore

Day = Annotated[str, Field(description="A date as YYYY-MM-DD, for example 2026-09-01")]


@lru_cache(maxsize=1)
def history() -> BatchStore:
    """The history, read once: the same batches the API loads."""
    return BatchStore.from_csv(DATA / "production_history.csv")


def covers() -> str:
    days = [b.shift_date for b in history().all()]
    return f"The history covers {min(days)} to {max(days)}."


@tool(name="scrap_rates", approval_mode="never_require",
      description="Every plant's scrap rate, as a percentage, for batches from start to end (both days included), "
                  "highest first. This app's definition: scrap square feet / square feet produced x 100. "
                  "Plants with no batches in those dates are left out.")
def scrap_rates(start: Day, end: Day) -> dict:
    """Every plant's scrap rate from start to end, highest first.

    PURPOSE     Questions about one plant, the best, the worst, or a ranking: one call answers them all.
    PSEUDOCODE  start, end not YYYY-MM-DD -> error asking for YYYY-MM-DD
                rates = scrap_rate_by_plant(the history, start, end), plants with no production left out
                none -> error saying which dates the history covers
                return the dates, the definition, and [{plant_id, scrap_rate_pct}] highest first
    """
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError:
        return {"error": f"Dates must be YYYY-MM-DD; got start={start!r}, end={end!r}."}
    rates = {p: r for p, r in scrap_rate_by_plant(history().all(), first, last).items() if r is not None}
    if not rates:
        return {"error": f"No batches from {first} to {last}. {covers()}"}
    ranked = sorted(rates.items(), key=lambda pr: (-pr[1], pr[0]))
    return {"start": str(first), "end": str(last),
            "definition": "scrap square feet / square feet produced x 100",
            "rates": [{"plant_id": p, "scrap_rate_pct": r} for p, r in ranked]}


@tool(name="check_batch_file", approval_mode="never_require",
      description="Run every quality rule on a batch file in the app's data folder, as an upload would, without "
                  "loading it. Returns how many batches it has, how many pass, each failing batch with the rule it "
                  "breaks, and whether the file would load (only if every batch passes).")
def check_batch_file(
    file_name: Annotated[str, Field(description="A file name only, such as batch_2026-10-01.csv; no folders")],
) -> dict:
    """Check a batch file in data/ against every rule, without loading it.

    PURPOSE     "Would this file load, and if not, why?" answered the way POST /imports would answer it.
    PSEUDOCODE  file_name must be a bare name of a .csv that exists in data/ -> else error
                (the model chooses the argument: never let it reach outside data/)
                batches = read it; not a batch file -> error
                results = check(batches) with the SKU list, the machine list and the history's BatchIds
                return the counts, would_load, and {batch_id, rule} for every batch that breaks a rule
    """
    path = DATA / file_name
    if Path(file_name).name != file_name or not file_name.endswith(".csv") or not path.is_file():
        return {"error": f"{file_name!r} isn't a batch file in the data folder. Give a file name only, "
                         "such as batch_2026-10-01.csv."}
    try:
        batches = read_batches(path)
    except (KeyError, ValueError) as e:
        return {"error": f"{file_name} isn't a batch file: {e}"}
    results = check(batches, sku_ids=load_sku_ids(), asset_plants=load_asset_plants(),
                    loaded_ids=history().batch_ids())
    failures = [{"batch_id": b.batch_id, "rule": rule} for rule, broken in results.items() for b in broken]
    bad = failing_ids(results)
    passed = sum(1 for b in batches if b.batch_id not in bad)
    return {"file": file_name, "batches": len(batches), "pass": passed, "would_load": not failures,
            "failures": failures}


@tool(name="square_feet_per_run_hour", approval_mode="never_require",
      description="Every plant's square feet produced per run hour, for batches from start to end (both days "
                  "included), highest first. Definition: total square feet produced / total run hours, the same "
                  "as the data team's Square Feet per Run Hour measure. Plants with no run hours are left out.")
def square_feet_per_run_hour(start: Day, end: Day) -> dict:
    """Every plant's square feet per run hour from start to end, highest first.

    PURPOSE     How much board each plant runs per hour of machine time, by the definition Ops_Model uses.
    PSEUDOCODE  start, end not YYYY-MM-DD -> error asking for YYYY-MM-DD
                rates = square_feet_per_run_hour_by_plant(the history, start, end), plants with no run hours left out
                none -> error saying which dates the history covers
                return the dates, the definition, and [{plant_id, square_feet_per_run_hour}] highest first
    """
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError:
        return {"error": f"Dates must be YYYY-MM-DD; got start={start!r}, end={end!r}."}
    rates = {p: r for p, r in square_feet_per_run_hour_by_plant(history().all(), first, last).items() if r is not None}
    if not rates:
        return {"error": f"No batches from {first} to {last}. {covers()}"}
    ranked = sorted(rates.items(), key=lambda pr: (-pr[1], pr[0]))
    return {"start": str(first), "end": str(last), "definition": "total square feet produced / total run hours",
            "rates": [{"plant_id": p, "square_feet_per_run_hour": r} for p, r in ranked]}


TOOLS = [scrap_rates, check_batch_file, square_feet_per_run_hour]
