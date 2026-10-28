"""Tests for POST /ask: the app puts the hosted assistant in front of its users.

PURPOSE  The route is tested with a stand-in for the hosted agent, so the tests run offline: what the app sends,
         what it returns, and what it says when the assistant isn't set up or fails.
"""

from fastapi.testclient import TestClient

from plant_ops.api import create_app

QUESTION = "What was P01's scrap rate in September 2026?"


def test_ask_returns_the_assistants_answer():
    asked = []
    app = create_app(ask=lambda q: asked.append(q) or "5.99%, by this app's definition.")
    response = TestClient(app).post("/ask", json={"question": QUESTION})
    assert response.status_code == 200
    assert response.json() == {"question": QUESTION, "answer": "5.99%, by this app's definition."}
    assert asked == [QUESTION]


def test_an_empty_question_is_422():
    response = TestClient(create_app(ask=lambda q: "never asked")).post("/ask", json={"question": ""})
    assert response.status_code == 422


def test_an_assistant_failure_is_502():
    def broken(question):
        raise RuntimeError("the hosted agent is not active")

    response = TestClient(create_app(ask=broken)).post("/ask", json={"question": QUESTION})
    assert response.status_code == 502
    assert "assistant" in response.json()["detail"].lower()


def test_without_its_settings_ask_is_503(monkeypatch):
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("PLANT_OPS_AGENT_NAME", raising=False)
    response = TestClient(create_app()).post("/ask", json={"question": QUESTION})
    assert response.status_code == 503
    assert "FOUNDRY_PROJECT_ENDPOINT" in response.json()["detail"]
    assert "PLANT_OPS_AGENT_NAME" in response.json()["detail"]
