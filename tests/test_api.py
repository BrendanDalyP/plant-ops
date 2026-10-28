"""Tests for the web API.

PURPOSE  Call the app the way a browser or another service would, through FastAPI's TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from plant_ops.api import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health_reports_the_history(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "batches": 1943}


def test_scrap_rate_for_a_plant(client):
    response = client.get("/plants/P01/scrap-rate", params={"start": "2026-09-01", "end": "2026-09-30"})
    assert response.status_code == 200
    assert response.json()["plant_id"] == "P01"


def test_unknown_plant_is_404(client):
    response = client.get("/plants/P99/scrap-rate", params={"start": "2026-09-01", "end": "2026-09-30"})
    assert response.status_code == 404
