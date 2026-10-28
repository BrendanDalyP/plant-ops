"""Tests for the agent's wiring: its instructions, its tools, and what goes back to the model.

PURPOSE  Check the agent the way it is built everywhere (build_agent), with ScriptedModel in place of Foundry.
"""

import asyncio

from agent_framework.foundry import FoundryToolbox


def ask(agent, question):
    return asyncio.run(agent.run(question))


def test_the_agent_answers_through_the_model_it_is_given(agent_module, scripted_model):
    model = scripted_model("I answer questions about production at the plants.")
    reply = ask(agent_module.build_agent(client=model), "What can you do?")
    assert reply.text == "I answer questions about production at the plants."


def test_the_instructions_keep_it_to_production(agent_module, scripted_model):
    model = scripted_model("Hello.")
    ask(agent_module.build_agent(client=model), "Hi")
    assert "production" in model.instructions().lower()


def test_the_model_is_offered_both_tools(agent_module, tools, scripted_model):
    model = scripted_model("Hello.")
    ask(agent_module.build_agent(client=model), "Hi")
    assert {"scrap_rates", "check_batch_file"} <= model.offered_tools()


def test_a_tool_result_goes_back_to_the_model(agent_module, tools, scripted_model):
    model = scripted_model(("scrap_rates", {"start": "2026-09-01", "end": "2026-09-30"}),
                           "P01's scrap rate in September 2026 was 5.99%.")
    reply = ask(agent_module.build_agent(client=model), "What was P01's scrap rate in September 2026?")
    assert '"P01"' in model.tool_results()[0] and "5.99" in model.tool_results()[0]
    assert "5.99" in reply.text


def test_no_toolbox_without_toolbox_endpoint(agent_module, scripted_model, monkeypatch):
    monkeypatch.delenv("TOOLBOX_ENDPOINT", raising=False)
    agent = agent_module.build_agent(client=scripted_model())
    assert not any(isinstance(t, FoundryToolbox) for t in agent.mcp_tools)


def test_the_class_toolbox_when_toolbox_endpoint_is_set(agent_module, scripted_model, monkeypatch):
    url = "https://example.services.ai.azure.com/api/projects/p/toolboxes/ops-tools/versions/1/mcp?api-version=v1"
    monkeypatch.setenv("TOOLBOX_ENDPOINT", url)
    agent = agent_module.build_agent(client=scripted_model())
    toolboxes = [t for t in agent.mcp_tools if isinstance(t, FoundryToolbox)]
    assert len(toolboxes) == 1, "Part 4: add FoundryToolbox to the agent's tools when TOOLBOX_ENDPOINT is set"
