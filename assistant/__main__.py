"""
python -m assistant · Ask the Plant Ops assistant one question from the terminal.
PURPOSE  The quickest way to try the agent on the real model while you build it; --trace also sends the run's
         trace to the Foundry project, where you can follow each model call and tool call.
PSEUDOCODE
  load .env
  agent = build_agent()
  --trace: send traces to the project's Application Insights, prompts and answers included (a class project only)
  print the agent's answer to the question
RUN      python -m assistant [--trace] "What was P01's scrap rate in September 2026?"
"""

import asyncio
import sys

from dotenv import load_dotenv

from assistant.agent import build_agent


async def main(question: str, trace: bool) -> None:
    agent = build_agent()
    if trace:
        await agent.client.configure_azure_monitor(enable_sensitive_data=True)
    reply = await agent.run(question)
    print(reply.text)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--trace"]
    if len(args) != 1:
        sys.exit('usage: python -m assistant [--trace] "<question>"')
    load_dotenv()
    asyncio.run(main(args[0], trace="--trace" in sys.argv[1:]))
