"""Tests for deploy/deploy_agent.py, without deploying anything.

PURPOSE  What gets uploaded to Foundry, and how the hosted agent is told to run, are checked here before anyone
         runs the deployment: the zip holds the code the agent needs and no secrets, and the definition runs
         main.py on Python 3.13 with the settings it needs.
"""

import importlib.util
import io
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def deploy():
    spec = importlib.util.spec_from_file_location("deploy_agent", ROOT / "deploy" / "deploy_agent.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def names(deploy):
    return set(zipfile.ZipFile(io.BytesIO(deploy.code_zip())).namelist())


def test_the_zip_holds_what_the_agent_runs(deploy):
    assert {"main.py", "requirements.txt", "assistant/agent.py", "assistant/tools.py", "plant_ops/rules.py",
            "data/production_history.csv", "data/batch_2026-10-01.csv"} <= names(deploy)


def test_the_zip_leaves_out_secrets_tests_and_git(deploy):
    for name in names(deploy):
        assert not name.startswith((".env", "tests/", ".git/", ".github/", ".devcontainer/", "deploy/")), name
        assert "__pycache__" not in name and not name.endswith(".pyc"), name


def test_the_definition_runs_main_py_on_python_3_13(deploy, monkeypatch):
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4-mini")
    monkeypatch.delenv("TOOLBOX_ENDPOINT", raising=False)
    d = deploy.definition()
    code = d.code_configuration
    assert (code.runtime, code.entry_point, code.dependency_resolution) == ("python_3_13", ["python", "main.py"],
                                                                          "remote_build")
    assert [p.protocol for p in d.protocol_versions] == ["responses"]
    assert d.environment_variables == {"AZURE_AI_MODEL_DEPLOYMENT_NAME": "gpt-5.4-mini", "PYTHONNOUSERSITE": "1"}


def test_the_definition_passes_the_toolbox_when_it_is_set(deploy, monkeypatch):
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4-mini")
    monkeypatch.setenv("TOOLBOX_ENDPOINT", "https://example/toolboxes/ops-tools/versions/1/mcp")
    assert deploy.definition().environment_variables["TOOLBOX_ENDPOINT"].endswith("/ops-tools/versions/1/mcp")


def test_the_upload_is_a_zip_named_for_the_agent(deploy, monkeypatch):
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4-mini")
    sent = {}

    class Agents:  # stands in for project.agents: records what would be uploaded
        def create_version_from_code(self, name, *, definition, code, description=None):
            sent.update(name=name, file=code.name, files=set(zipfile.ZipFile(code).namelist()))
            return type("Created", (), {"version": "3"})()

    project = type("Project", (), {"agents": Agents()})()
    assert deploy.upload(project, "plant-ops-bd") == "3"
    assert (sent["name"], sent["file"]) == ("plant-ops-bd", "plant-ops-bd.zip")
    assert {"main.py", "requirements.txt", "assistant/agent.py"} <= sent["files"]


def test_requirements_txt_pins_what_requirements_dev_pins():
    def pins(name):
        return [ln.strip() for ln in (ROOT / name).read_text().splitlines() if ln.strip() and not ln.startswith("#")]

    dev, hosted = set(pins("requirements-dev.txt")), pins("requirements.txt")
    assert hosted, "requirements.txt is empty"
    for pin in hosted:
        assert "==" in pin and pin in dev, f"{pin} isn't pinned the same in requirements-dev.txt"
