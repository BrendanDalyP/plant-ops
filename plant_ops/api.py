"""The Plant Ops web API.

PURPOSE  Answer the plant managers' questions over HTTP.
RUN      uvicorn plant_ops.api:create_app --factory --reload
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException

from plant_ops.reference_data import DATA
from plant_ops.stats import scrap_rate_by_plant
from plant_ops.store import BatchStore


def create_app(history_csv: str | Path = DATA / "production_history.csv") -> FastAPI:
    """Build the app around a store loaded from the history file.

    PURPOSE     One place that wires the store and the routes together. Tests build a fresh app each time.
    PSEUDOCODE  store = every batch in history_csv
                GET /health                    -> status and how many batches are loaded
                GET /plants/{id}/scrap-rate    -> that plant's scrap rate from start to end, or 404
    """
    store = BatchStore.from_csv(history_csv)
    app = FastAPI(title="Plant Ops")
    app.state.store = store

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "batches": len(store.all())}

    @app.get("/plants/{plant_id}/scrap-rate")
    def plant_scrap_rate(plant_id: str, start: date, end: date) -> dict:
        """A plant's scrap rate, as a percentage, from start to end (both days included).

        PURPOSE     The number on the plant managers' report.
        PSEUDOCODE  rates = scrap_rate_by_plant(every loaded batch, start, end)
                    the plant has no batches in the period -> 404; else return its rate
        """
        rates = scrap_rate_by_plant(store.all(), start, end)
        if plant_id not in rates:
            raise HTTPException(status_code=404, detail=f"No batches for {plant_id} from {start} to {end}")
        return {"plant_id": plant_id, "start": start, "end": end, "scrap_rate_pct": rates[plant_id]}

    return app
