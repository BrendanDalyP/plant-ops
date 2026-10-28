"""
python -m assistant · Ask the Plant Ops assistant one question from the terminal.
PURPOSE  The quickest way to try the agent on the real model while you build it.
PSEUDOCODE
  load .env
  agent = build_agent()
  print the agent's answer to the question
RUN      python -m assistant "What was P01's scrap rate in September 2026?"
"""

import asyncio
import sys

from dotenv import load_dotenv

from assistant.agent import build_agent


async def main(question: str) -> None:
    agent = build_agent()
    reply = await agent.run(question)
    print(reply.text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('usage: python -m assistant "<question>"')
    load_dotenv()
    asyncio.run(main(sys.argv[1]))
