"""
main.py · The Plant Ops assistant as a Foundry hosted agent.
PURPOSE  Foundry runs this file in the hosted agent's container, where it serves build_agent() over the Responses
         protocol. Run it here and it serves the same agent on http://localhost:8088/responses.
PSEUDOCODE
  load .env if there is one (here; in Foundry the platform and deploy_agent.py set the environment)
  serve build_agent(hosted=True) with ResponsesHostServer, which keeps each conversation's history
RUN      python main.py
"""

from agent_framework_foundry_hosting import ResponsesHostServer
from dotenv import load_dotenv

from assistant.agent import build_agent

if __name__ == "__main__":
    load_dotenv()
    ResponsesHostServer(build_agent(hosted=True)).run()
