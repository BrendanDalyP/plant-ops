"""
deploy_agent.py · Deploy the assistant to Foundry Agent Service as a hosted agent. Finished in Part 7.
PURPOSE  Upload this repo's code. Foundry installs requirements.txt, runs main.py and serves the agent; this script
         then sends all of the agent's traffic to the new version.
PSEUDOCODE
  code_zip()     a zip, in memory, of main.py, requirements.txt, assistant/, plant_ops/ and data/*.csv, at the same
                 paths as in the repo, and nothing else: no .env, tests/, .git/, .github/ or __pycache__/
  definition()   a HostedAgentDefinition:
                   code: runtime python_3_13, entry point python main.py, dependencies built remotely
                   protocol: responses, version 2.0.0; cpu 0.5, memory 1Gi
                   environment: AZURE_AI_MODEL_DEPLOYMENT_NAME, PYTHONNOUSERSITE=1 (only the agent's own packages),
                   and TOOLBOX_ENDPOINT when it is set (FOUNDRY_PROJECT_ENDPOINT comes from the platform: don't send it)
  upload(project, name)
                 create a version of the agent from code_zip() and definition(); the SDK takes the zip as a
                 stream whose name ends in .zip, so name it <name>.zip; return the new version
  main()         load .env; sign in as you (DefaultAzureCredential); version = upload(the project, PLANT_OPS_AGENT_NAME)
                 every 10 seconds, for at most 10 minutes, read its status: active -> go on; failed -> stop with it
                 send 100% of the agent endpoint's traffic to that version, over the responses protocol
                 print the agent's name and version, and where to try it in the Foundry portal
RUN      python deploy/deploy_agent.py
"""


def code_zip() -> bytes:
    raise NotImplementedError("deploy_agent.py: write code_zip() (Part 7)")


def definition():
    raise NotImplementedError("deploy_agent.py: write definition() (Part 7)")


def upload(project, name: str) -> str:
    raise NotImplementedError("deploy_agent.py: write upload() (Part 7)")


def main() -> None:
    raise NotImplementedError("deploy_agent.py: write main() (Part 7)")


if __name__ == "__main__":
    main()
