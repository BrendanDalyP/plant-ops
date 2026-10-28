"""
day5app.py · Day 5's app path: starter files, setup, catch-up and an environment check.
PURPOSE  One script for the app path, run straight from the checkpoint you want, so it is always that checkpoint's
         version:  git show origin/checkpoint/5a-0:scripts/day5app.py | python3 - start
PSEUDOCODE
  start        copy checkpoint/5a-0's new files that you don't have yet, and its versions of the three files
               Day 4 never changed (the Codespace's settings, requirements-dev.txt, .gitignore); commit
  setup        pip install -r requirements-dev.txt; the Azure Developer CLI and its microsoft.foundry
               extension, if missing; .env from .env.example, if there's no .env
  catch-up N   restore every file in checkpoint/5a-N, except your cheat sheet, your gotchas log and .env; commit
  doctor       check the packages, the CLIs, your sign-in and .env; then ask the Foundry project which models it
               has deployed. Each line says OK or MISSING, and how to fix what's missing
NOTE     catch-up replaces your files with the reference ones, as Day 4's catch-up did. Commit first to keep yours
         in the branch's history. Files you added that the checkpoint doesn't have are left alone.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

KEEP = {"cheat-sheet.md", "docs/copilot-gotchas.md", ".env"}
STARTER = ("scripts/day5app.py", "assistant/__init__.py", "tests/assistant/", "docs/assistant.md", ".env.example",
           "deploy/deploy_agent.py", ".github/ISSUE_TEMPLATE/assistant-tool.md")
REPLACE = (".devcontainer/devcontainer.json", "requirements-dev.txt", ".gitignore")
SETTINGS = ("FOUNDRY_PROJECT_ENDPOINT", "AZURE_AI_MODEL_DEPLOYMENT_NAME")


def git(*args, binary=False):
    """Run git in the current repo; stop with its message if it fails."""
    r = subprocess.run(["git", *args], capture_output=True, check=False)
    if r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr.decode(errors='replace')}")
    return r.stdout if binary else r.stdout.decode()


def checkpoint(n):
    """The ref for checkpoint/5a-N: the remote branch if you have it, else a local branch."""
    n = n.split("-")[-1]
    for ref in (f"origin/checkpoint/5a-{n}", f"checkpoint/5a-{n}"):
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref], capture_output=True,
                          check=False).returncode == 0:
            return ref
    sys.exit(f"checkpoint/5a-{n} not found: run git fetch (or see 'Fall behind?' in the guide)")


def files_at(ref):
    return git("ls-tree", "-r", "--name-only", ref).splitlines()


def commit(message):
    git("add", "-A")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], check=False).returncode:
        git("commit", "-q", "-m", message)
        print(f"committed: {message}. Now push.")
    else:
        print("nothing to change: you're already there")


def start():
    src, changed = checkpoint("0"), []
    for path in files_at(src):
        if (path.startswith(STARTER) and not Path(path).exists()) or path in REPLACE:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(git("show", f"{src}:{path}", binary=True))
            changed.append(path)
    print("added or updated:", *changed, sep="\n  ")
    commit("Day 5 app path: starter files")


def catch_up(n):
    src = checkpoint(n)
    paths = [p for p in files_at(src) if p not in KEEP]
    for i in range(0, len(paths), 200):
        git("restore", f"--source={src}", "--staged", "--worktree", "--", *paths[i:i + 200])
    commit(f"Catch up to {src.removeprefix('origin/')}")


def run(cmd):
    """Run a command; return its first line of output, or None if it failed or isn't installed."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None
    lines = (r.stdout + r.stderr).strip().splitlines()
    return (lines[0] if lines else "ok") if r.returncode == 0 else None


def setup():
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-dev.txt"], check=True)
    if not shutil.which("azd"):
        subprocess.run("curl -fsSL https://aka.ms/install-azd.sh | bash", shell=True, check=True)
    if "microsoft.foundry" not in json.dumps(extensions()):
        subprocess.run(["azd", "extension", "install", "microsoft.foundry"], check=False)
    if not Path(".env").exists():
        shutil.copy(".env.example", ".env")
        print("made .env from .env.example: fill it in from the board")
    doctor()


def extensions():
    """The azd extensions installed here, or [] if azd is missing."""
    try:
        r = subprocess.run(["azd", "extension", "list", "--installed", "--output", "json"],
                           capture_output=True, text=True, check=False)
        return json.loads(r.stdout or "[]")
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def dotenv():
    """The settings in .env, without needing python-dotenv."""
    values = {}
    if Path(".env").exists():
        for line in Path(".env").read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"')
    return values


def doctor():
    env = {**dotenv(), **{k: v for k, v in os.environ.items() if k in SETTINGS}}
    probe = "from importlib.metadata import version as v; print('agent-framework-core', v('agent-framework-core'))"
    packages = run([sys.executable, "-c", probe])
    foundry_ext = "microsoft.foundry" in json.dumps(extensions())
    checks = [
        ("agent packages", packages, "python3 scripts/day5app.py setup"),
        ("Azure CLI sign-in", run(["az", "account", "show", "--query", "user.name", "--output", "tsv"]),
         "az login --use-device-code --tenant <tenant ID from the board>"),
        ("Azure Developer CLI", run(["azd", "version"]), "python3 scripts/day5app.py setup"),
        ("azd Foundry extension", "microsoft.foundry" if foundry_ext else None, "azd extension install microsoft.foundry"),
    ]
    for name in SETTINGS:
        value = env.get(name, "")
        checks.append((name, value if value and "<" not in value else None, f"set {name} in .env from the board"))
    for name, found, fix in checks:
        print(f"{'OK     ' if found else 'MISSING'} {name:30} {found or 'fix: ' + fix}")
    if all(found for _, found, _ in checks):
        foundry(env)
    toolbox = env.get("TOOLBOX_ENDPOINT") or dotenv().get("TOOLBOX_ENDPOINT")
    print(f"{'OK     ' if toolbox else 'LATER  '} {'TOOLBOX_ENDPOINT':30} {toolbox or 'Part 4 sets it'}")


def foundry(env):
    """Sign in as you and list the project's model deployments: proves the endpoint, the role and the model."""
    from azure.ai.projects import AIProjectClient
    from azure.core.exceptions import AzureError
    from azure.identity import DefaultAzureCredential

    try:
        with AIProjectClient(endpoint=env["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()) as p:
            names = sorted(d.name for d in p.deployments.list())
    except (AzureError, ValueError) as e:  # a setup problem to report, not a crash
        print(f"MISSING {'Foundry project':30} {type(e).__name__}: {str(e).splitlines()[0][:150]}")
        print(f"        {'':30} fix: check the endpoint, az login, and that you're Foundry User on the project")
        return
    model = env["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    found = model in names
    print(f"{'OK     ' if found else 'MISSING'} {'model deployment':30} {model if found else 'not in ' + str(names)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["start"]:
        start()
    elif args[:1] == ["setup"]:
        setup()
    elif args[:1] == ["catch-up"] and len(args) == 2:
        catch_up(args[1])
    elif args[:1] == ["doctor"]:
        doctor()
    else:
        sys.exit(__doc__)
