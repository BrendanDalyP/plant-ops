"""The Plant Ops web API.

PURPOSE  Answer the plant managers' questions over HTTP, and take in the plants' batch files.
RUN      uvicorn plant_ops.api:create_app --factory --reload
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from plant_ops.batches import parse_batches
from plant_ops.reference_data import DATA, load_asset_plants, load_sku_ids
from plant_ops.rules import check
from plant_ops.stats import scrap_rate_by_plant
from plant_ops.store import BatchStore


class Question(BaseModel):
    question: str = Field(min_length=1, description="A question about production, in plain English")


def hosted_assistant() -> Callable[[str], str] | None:
    """The hosted assistant from Part 7, as a function from question to answer; None if it isn't set up.

    PURPOSE     The app's way in to the Foundry hosted agent, signed in as whoever runs the app.
    PSEUDOCODE  FOUNDRY_PROJECT_ENDPOINT or PLANT_OPS_AGENT_NAME not set -> None
                ask(question) = the hosted agent's answer, over the Responses protocol, signed in with
                                DefaultAzureCredential (your az login here; a managed identity in Azure)
    """
    endpoint, name = os.environ.get("FOUNDRY_PROJECT_ENDPOINT"), os.environ.get("PLANT_OPS_AGENT_NAME")
    if not (endpoint and name):
        return None

    def ask(question: str) -> str:
        from azure.ai.projects import AIProjectClient  # only POST /ask needs Azure's packages
        from azure.identity import DefaultAzureCredential

        with (DefaultAzureCredential() as credential,
              AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True) as project,
              project.get_openai_client(agent_name=name) as openai):
            return openai.responses.create(input=question).output_text

    return ask


def create_app(history_csv: str | Path = DATA / "production_history.csv",
               ask: Callable[[str], str] | None = None) -> FastAPI:
    """Build the app around a store loaded from the history file.

    PURPOSE     One place that wires the store, the reference data and the routes together. Tests build a
                fresh app each time.
    PSEUDOCODE  store = every batch in history_csv; load the SKU and machine lists once
                GET  /health                   -> status and how many batches are loaded
                GET  /plants/{id}/scrap-rate   -> that plant's scrap rate from start to end, or 404
                POST /imports                  -> run every rule on an uploaded batch file;
                                                  all pass: load it (201); any fail: load nothing (422)
                POST /ask                      -> the assistant's answer to a question: ask, or the hosted
                                                  assistant when the environment names it (Part 7)
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

    @app.post("/ask")
    def ask_assistant(body: Question) -> dict:
        """Ask the Plant Ops assistant a question in plain English.

        PURPOSE     Plant managers ask in words instead of building a URL; the hosted agent answers.
        PSEUDOCODE  answerer = ask, or the hosted assistant; neither -> 503 naming the settings it needs
                    answer = answerer(question); it fails -> 502, so a broken assistant never looks like a bad question
                    return the question and the answer
        """
        answerer = ask or hosted_assistant()
        if answerer is None:
            raise HTTPException(status_code=503, detail="The assistant isn't set up: set FOUNDRY_PROJECT_ENDPOINT "
                                                        "and PLANT_OPS_AGENT_NAME")
        try:
            answer = answerer(body.question)
        except Exception as e:  # whatever went wrong is the assistant's, not the caller's
            raise HTTPException(status_code=502, detail=f"The assistant failed: {e}") from e
        return {"question": body.question, "answer": answer}

    return app
