"""The Plant Ops assistant: an agent that answers plant managers' questions.

PURPOSE  The one place the agent is built: its model, its instructions and its tools. The terminal, the tests, the
         evaluations and the hosted agent all call build_agent(), so they all run the same agent.
"""

from __future__ import annotations

import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

NAME = "plant-ops-assistant"

INSTRUCTIONS = """You are the Plant Ops assistant. You answer plant managers' questions about production at the
company's eight corrugated packaging plants, P01 to P08: batches, scrap, and whether batch files pass the
quality rules.

- Answer from your tools, never from memory or a guess. If no tool can answer, say so, and say what you'd need.
- Give numbers as the tools return them, with their units and the dates they cover.
- You answer production questions only. To anything else, say that you answer questions about production only.
- Be brief: a sentence or two, then the numbers."""


def build_agent(client=None, *, credential=None) -> Agent:
    """Build the assistant.

    PURPOSE     The same agent everywhere: tests hand it a scripted stand-in for the model; everything else gets
                the Foundry project's model.
    PSEUDOCODE  client = the one given, or the model deployment named in the environment, in the Foundry project
                         named in the environment, signed in as you
                return an Agent with the name and instructions above, and no tools yet
    """
    credential = credential or DefaultAzureCredential()
    if client is None:
        client = FoundryChatClient(project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
                                   model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"], credential=credential)
    return Agent(client=client, name=NAME, instructions=INSTRUCTIONS)
