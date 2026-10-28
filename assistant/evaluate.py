"""
python -m assistant.evaluate · Score the assistant on the questions in evals/questions.yaml.
PURPOSE  An agent is code you test. The same questions, scored the same way, before every deployment: locally for
         the numbers and the tools, and with --foundry by Foundry's own evaluators as well.
PSEUDOCODE
  load_questions()  the items in evals/questions.yaml: question; expect = what a right answer contains;
                    tools = the tools it must call; needs: ops-agent = only when TOOLBOX_ENDPOINT is set
  score(agent, items, foundry=False)
                    run each question through the agent with evaluate_agent, scored locally:
                      says_what_it_must   every expect string is in the answer
                      tool_calls_present  every listed tool was called
                    foundry: also Foundry's evaluators (task adherence, tool call accuracy, relevance)
  main              load .env; agent = build_agent(); keep the items this setup can answer; score them
                    print one line per question per scorer, the totals and Foundry's report link
                    exit 1 if anything failed
RUN      python -m assistant.evaluate [--foundry]
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from agent_framework import ExpectedToolCall, LocalEvaluator, evaluate_agent, evaluator, tool_calls_present

QUESTIONS = Path(__file__).resolve().parent.parent / "evals" / "questions.yaml"


def load_questions(path: Path = QUESTIONS) -> list[dict]:
    """Every item in the questions file, with tools and needs filled in when an item leaves them out."""
    import yaml  # only the evaluations need it, not the hosted agent

    items = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [{"tools": [], "needs": None, **item} for item in items]


@evaluator
def says_what_it_must(response: str, expected_output: str) -> bool:
    """Every line of expected_output appears in the answer."""
    return all(e in response for e in expected_output.splitlines())


async def score(agent, items: list[dict], foundry: bool = False) -> list:
    """Run the items through the agent and score the answers.

    PURPOSE     The same questions, scored the same way, for any agent: the real one, or one with a stand-in model.
    PSEUDOCODE  scorers = local checks (says_what_it_must, tool_calls_present), plus Foundry's judges if foundry
                return evaluate_agent(the agent, each question, its expect lines, its tools): one result set per
                scorer, local first
    """
    scorers = [LocalEvaluator(says_what_it_must, tool_calls_present)]
    if foundry:
        from agent_framework.foundry import FoundryEvals

        scorers.append(FoundryEvals(client=agent.client, model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
                                    evaluators=[FoundryEvals.TASK_ADHERENCE, FoundryEvals.TOOL_CALL_ACCURACY,
                                                FoundryEvals.RELEVANCE]))
    return await evaluate_agent(
        agent=agent, eval_name="plant-ops-assistant", evaluators=scorers,
        queries=[i["question"] for i in items],
        expected_output=["\n".join(i["expect"]) for i in items],
        expected_tool_calls=[[ExpectedToolCall(t) for t in i["tools"]] for i in items])


async def main(foundry: bool) -> int:
    from assistant.agent import build_agent

    items = [i for i in load_questions() if i["needs"] != "ops-agent" or os.environ.get("TOOLBOX_ENDPOINT")]
    results = await score(build_agent(), items, foundry=foundry)
    for result in results:
        print(f"\n{result.provider}: {result.passed} of {result.total} passed")
        for item, question in zip(result.items, items):
            print(f"  {'PASS' if item.passed else 'FAIL'}  {question['question']}")
            if not item.passed:
                print(f"        answer: {item.response[:300]!r}")
        if result.report_url:
            print(f"  report: {result.report_url}")
    return 0 if all(r.all_passed for r in results) else 1


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    sys.exit(asyncio.run(main(foundry="--foundry" in sys.argv[1:])))
