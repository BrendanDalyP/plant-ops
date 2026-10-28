"""The Plant Ops assistant: an agent that answers plant managers' questions.

PURPOSE  The one place the agent is built: its model, its instructions and its tools. The terminal, the tests, the
         evaluations and the hosted agent all call build_agent(), so they all run the same agent.
"""

from __future__ import annotations

import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient, FoundryToolbox
from azure.identity import DefaultAzureCredential

from assistant.tools import TOOLS

NAME = "plant-ops-assistant"

INSTRUCTIONS = """You are the Plant Ops assistant. You answer plant managers' questions about production at the
company's eight corrugated packaging plants, P01 to P08: batches, scrap, and whether batch files pass the
quality rules.

- Answer from your tools, never from memory or a guess. If no tool can answer, say so, and say what you'd need.
- Give numbers as the tools return them, with their units and the dates they cover.
- You answer production questions only. To anything else, say that you answer questions about production only.
- Be brief: a sentence or two, then the numbers.

Two sources, two definitions of scrap rate:
- Your scrap_rates tool uses this app's history (September 2026 only) and this app's definition: scrap square
  feet / square feet produced.
- Ops_Agent, in your toolbox, uses the company's 33 months and the company's Scrap Rate %: scrap square feet /
  (square feet produced + scrap square feet).
Use your own tools first. Ask Ops_Agent for anything they can't answer, such as other months. Every time you give
a scrap rate, say which source and which definition it comes from, and never compare numbers from the two
sources without saying that they're defined differently."""


def build_agent(client=None, *, credential=None, hosted=False) -> Agent:
    """Build the assistant.

    PURPOSE     The same agent everywhere: tests hand it a scripted stand-in for the model; everything else gets
                the Foundry project's model.
    PSEUDOCODE  client = the one given, or the model deployment named in the environment, in the Foundry project
                         named in the environment, signed in as you
                tools = this app's tools, plus the class's Foundry toolbox (Ops_Agent) when TOOLBOX_ENDPOINT is set
                hosted: the host keeps the conversation, so the model service mustn't store it as well
                return an Agent with the name, the instructions above and those tools
    """
    credential = credential or DefaultAzureCredential()
    if client is None:
        client = FoundryChatClient(project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
                                   model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"], credential=credential)
    tools = [*TOOLS]
    if os.environ.get("TOOLBOX_ENDPOINT"):
        tools.append(FoundryToolbox(credential))  # reads TOOLBOX_ENDPOINT; signs every call in with credential
    options = {"default_options": {"store": False}} if hosted else {}
    return Agent(client=client, name=NAME, instructions=INSTRUCTIONS, tools=tools, **options)
