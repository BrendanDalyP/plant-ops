"""Test the assistant without a model: a scripted stand-in, so no test calls Foundry.

PURPOSE  The tests in tests/assistant check the agent's wiring (its instructions, the tools it offers, what a tool
         sends back) and the tools' numbers. A real model answers differently every time and costs money, so
         the tests use ScriptedModel instead, offline. The real model is checked by the evaluations (Part 5).
PSEUDOCODE
  ScriptedModel(*replies)  each time the agent calls the model, give the next reply:
                             ("tool name", {arguments})  ->  the model asks to call that tool
                             "text"                      ->  the model answers with that text
                           and remember what the agent sent each time (messages, instructions, tools)
  scripted_model           fixture: the ScriptedModel class, so a test can script its own replies
  agent_module, tools, evaluate, deploy
                           fixtures: import that module, or fail with the part of the day that writes it
"""

import importlib
import json

import pytest
from agent_framework import (
    BaseChatClient,
    ChatResponse,
    ChatResponseUpdate,
    Content,
    FunctionInvocationLayer,
    Message,
    ResponseStream,
)


class ScriptedModel(FunctionInvocationLayer, BaseChatClient):
    """A stand-in for the Foundry model: plays back scripted replies and records what it was sent."""

    def __init__(self, *replies):
        super().__init__()
        self.replies = list(replies)
        self.calls = []  # one {"messages": [...], "options": {...}} per call, in order

    def _inner_get_response(self, *, messages, stream, options, **kwargs):
        self.calls.append({"messages": list(messages), "options": dict(options)})
        if not self.replies:
            raise AssertionError(f"the agent called the model {len(self.calls)} times; the test scripted fewer replies")
        reply, response_id = self.replies.pop(0), f"response-{len(self.calls)}"
        if isinstance(reply, tuple):
            name, arguments = reply
            content = Content.from_function_call(call_id=f"call-{len(self.calls)}", name=name,
                                                 arguments=json.dumps(arguments))
        else:
            content = Content.from_text(reply)

        async def respond():
            return ChatResponse(messages=[Message(role="assistant", contents=[content])], response_id=response_id)

        async def one_update():  # a hosted agent streams: here the whole reply arrives as one update
            yield ChatResponseUpdate(role="assistant", contents=[content], response_id=response_id)

        return ResponseStream(one_update(), finalizer=ChatResponse.from_updates) if stream else respond()

    def instructions(self):
        """The instructions the agent sent with its first call."""
        return self.calls[0]["options"].get("instructions") or ""

    def offered_tools(self):
        """The names of the tools the agent offered the model on its first call."""
        return {t.name for t in self.calls[0]["options"].get("tools") or []}

    def tool_results(self):
        """What each tool call sent back to the model, as text, in order."""
        last = self.calls[-1]["messages"]
        return [str(c.result) for m in last for c in m.contents if c.type == "function_result"]


def need(module, part):
    try:
        return importlib.import_module(module)
    except ModuleNotFoundError as e:
        if e.name == module:
            pytest.fail(f"{module.replace('.', '/')}.py not found: {part} writes it", pytrace=False)
        raise


@pytest.fixture
def scripted_model():
    return ScriptedModel


@pytest.fixture
def agent_module():
    return need("assistant.agent", "Part 2")


@pytest.fixture
def tools():
    return need("assistant.tools", "Part 3")


@pytest.fixture
def evaluate():
    return need("assistant.evaluate", "Part 5")
