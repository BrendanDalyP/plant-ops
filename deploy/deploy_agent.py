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

import io
import os
import sys
import time
import zipfile
from pathlib import Path

from azure.ai.projects.models import (
    CodeConfiguration,
    CodeDependencyResolution,
    HostedAgentDefinition,
    ProtocolVersionRecord,
)

ROOT = Path(__file__).resolve().parent.parent


def code_zip() -> bytes:
    """The code the hosted agent runs, zipped in memory: an allow-list, so nothing else can slip in."""
    files = [ROOT / "main.py", ROOT / "requirements.txt"]
    files += sorted(p for package in ("assistant", "plant_ops") for p in (ROOT / package).rglob("*.py"))
    files += sorted((ROOT / "data").glob("*.csv"))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(ROOT).as_posix())
    return buffer.getvalue()


def definition() -> HostedAgentDefinition:
    """How Foundry builds and runs the code: Python 3.13, python main.py, the Responses protocol."""
    env = {"AZURE_AI_MODEL_DEPLOYMENT_NAME": os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"], "PYTHONNOUSERSITE": "1"}
    if os.environ.get("TOOLBOX_ENDPOINT"):
        env["TOOLBOX_ENDPOINT"] = os.environ["TOOLBOX_ENDPOINT"]
    return HostedAgentDefinition(
        cpu="0.5",
        memory="1Gi",
        code_configuration=CodeConfiguration(runtime="python_3_13", entry_point=["python", "main.py"],
                                             dependency_resolution=CodeDependencyResolution.REMOTE_BUILD),
        protocol_versions=[ProtocolVersionRecord(protocol="responses", version="2.0.0")],
        environment_variables=env,
    )


def upload(project, name: str) -> str:
    """Create a version of the agent from this repo's code; return the version."""
    stream = io.BytesIO(code_zip())
    stream.name = f"{name}.zip"  # the SDK requires a stream whose name ends in .zip
    created = project.agents.create_version_from_code(
        name, definition=definition(), code=stream,
        description="The Plant Ops assistant, deployed by deploy/deploy_agent.py")
    return created.version


def main() -> None:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import (
        AgentEndpointConfig,
        FixedRatioVersionSelectionRule,
        ProtocolConfiguration,
        ResponsesProtocolConfiguration,
        VersionSelector,
    )
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    name = os.environ["PLANT_OPS_AGENT_NAME"]
    with (DefaultAzureCredential() as credential,
          AIProjectClient(endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project):
        version = upload(project, name)
        print(f"{name} version {version}: uploaded. Foundry is building it, which takes a few minutes.")
        for _ in range(60):
            time.sleep(10)
            details = project.agents.get_version(agent_name=name, agent_version=version)
            print(f"  {details['status']}")
            if details["status"] == "active":
                break
            if details["status"] == "failed":
                sys.exit(f"{name} version {version} failed: {dict(details)}")
        else:
            sys.exit(f"{name} version {version} isn't active after 10 minutes: check it in the Foundry portal")
        project.agents.update_details(agent_name=name, agent_endpoint=AgentEndpointConfig(
            version_selector=VersionSelector(version_selection_rules=[
                FixedRatioVersionSelectionRule(agent_version=version, traffic_percentage=100)]),
            protocol_configuration=ProtocolConfiguration(responses=ResponsesProtocolConfiguration())))
        print(f"{name} version {version} is live, with all of its traffic.")
        print(f"Try it: Foundry portal > your project > Agents > {name} > Playground")


if __name__ == "__main__":
    main()
