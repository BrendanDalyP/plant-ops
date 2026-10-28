"""Tests for main.py's host: the agent answers over the Responses protocol, as it will in Foundry.

PURPOSE  Before deploying, call the same server the hosted agent runs, in-process, with ScriptedModel as the model:
         the request Foundry sends goes in, the tool runs, and the answer and the tool's output come back.
"""

from agent_framework_foundry_hosting import ResponsesHostServer
from fastapi.testclient import TestClient


def test_the_host_answers_over_the_responses_protocol(agent_module, tools, scripted_model, monkeypatch):
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")  # a test sends no telemetry anywhere
    model = scripted_model(("scrap_rates", {"start": "2026-09-01", "end": "2026-09-30"}),
                           "P01's scrap rate in September 2026 was 5.99%, by this app's definition.")
    server = ResponsesHostServer(agent_module.build_agent(client=model, hosted=True))
    with TestClient(server) as client:
        response = client.post("/responses", json={"input": "What was P01's scrap rate in September 2026?",
                                                   "stream": False})
    body = response.json()
    assert (response.status_code, body["status"]) == (200, "completed")
    assert [o["type"] for o in body["output"]] == ["function_call", "function_call_output", "message"]
    assert "5.99" in body["output"][2]["content"][0]["text"]


def test_hosted_agents_leave_the_history_to_the_host(agent_module, scripted_model):
    assert agent_module.build_agent(client=scripted_model(), hosted=True).default_options["store"] is False
