"""The Plant Ops web API.

PURPOSE  Answer the plant managers' questions over HTTP, and take in the plants' batch files.
RUN      uvicorn plant_ops.api:create_app --factory --reload
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from plant_ops.batches import parse_batches
from plant_ops.reference_data import DATA, load_asset_plants, load_sku_ids
from plant_ops.rules import check
from plant_ops.stats import scrap_rate_by_plant
from plant_ops.store import BatchStore


def create_app(history_csv: str | Path = DATA / "production_history.csv") -> FastAPI:
    """Build the app around a store loaded from the history file.

    PURPOSE     One place that wires the store, the reference data and the routes together. Tests build a
                fresh app each time.
    PSEUDOCODE  store = every batch in history_csv; load the SKU and machine lists once
                GET  /health                   -> status and how many batches are loaded
                GET  /plants/{id}/scrap-rate   -> that plant's scrap rate from start to end, or 404
                POST /imports                  -> run every rule on an uploaded batch file;
                                                  all pass: load it (201); any fail: load nothing (422)
    """
    store = BatchStore.from_csv(history_csv)
    sku_ids, asset_plants = load_sku_ids(), load_asset_plants()
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

    @app.post("/imports", status_code=201)
    async def import_batches(file: UploadFile) -> dict:
        """Load an uploaded batch file whole, or not at all.

        PURPOSE     Plants send their day's batches here; only files that pass every rule are loaded.
        PSEUDOCODE  parse the upload; unreadable or empty -> 400
                    run every rule; any failure -> 422 with each failing batch and rule, nothing loaded
                    otherwise add every batch to the store -> 201 with the count
        """
        try:
            batches = parse_batches((await file.read()).decode("utf-8").splitlines())
        except (KeyError, ValueError, UnicodeDecodeError) as e:
            raise HTTPException(status_code=400, detail=f"Not a readable batch file: {e}") from e
        if not batches:
            raise HTTPException(status_code=400, detail="The file has no batches")
        results = check(batches, sku_ids=sku_ids, asset_plants=asset_plants, loaded_ids=store.batch_ids())
        failures = [{"batch_id": b.batch_id, "rule": rule} for rule, broken in results.items() for b in broken]
        if failures:  # all or nothing: one failing batch stops the whole file
            return JSONResponse(status_code=422, content={"accepted": 0, "failures": failures})
        store.add(batches)
        return {"accepted": len(batches)}

    return app
