"""
verify.py · Check a deployment: every notebook in the target workspace is bound to that workspace's lakehouse,
and no Dev workspace or lakehouse ID survived the deploy.
PURPOSE  A deploy that "succeeds" can still leave a notebook pointing at Dev. This reads what is actually in
         the target workspace and fails the job if anything still points elsewhere.
PSEUDOCODE
  target   = WORKSPACE_ID (env); token = a Fabric API token from the signed-in Azure CLI (azure/login)
  items    = every item in the target workspace (GET /workspaces/{id}/items, all pages)
  lakehouse= the target's Ops_Lakehouse id
  dev_ids  = every GUID in the META blocks of fabric/**/notebook-content.py (what Dev wrote to Git)
  for each notebook in the target:
      definition = POST getDefinition (a long-running operation: poll until it finishes)
      meta       = the notebook's lakehouse binding, read from its notebook-content.py part
      problems  += binding is not (target lakehouse, target workspace)
      problems  += any dev_id that appears anywhere in the definition
  print one line per notebook; exit 1 if there are problems
NOTE     Read-only: it never changes the workspace.
"""
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from azure.identity import AzureCliCredential

API = "https://api.fabric.microsoft.com/v1"
ROOT = Path(__file__).resolve().parents[1]
GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"


def meta_json(notebook_text):
    """The notebook-level META block of a notebook-content.py, as a dict (the first block in the file)."""
    lines, block = notebook_text.splitlines(), []
    start = lines.index("# METADATA ********************")
    for line in lines[start + 1:]:
        if line.startswith(("# CELL", "# MARKDOWN")):
            break
        if line.startswith("# META"):
            block.append(line[len("# META"):])
    return json.loads("\n".join(block))


def binding(notebook_text):
    """(default lakehouse id, its workspace id) from a notebook's META, or (None, None) when it has none."""
    lh = meta_json(notebook_text).get("dependencies", {}).get("lakehouse", {})
    return lh.get("default_lakehouse"), lh.get("default_lakehouse_workspace_id")


def dev_ids(repo_fabric_dir):
    """Every GUID in the META lines of the notebooks committed from Dev (what a deploy must not leave behind)."""
    ids = set()
    for f in Path(repo_fabric_dir).rglob("notebook-content.py"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("# META"):
                ids.update(g.lower() for g in re.findall(GUID, line))
    return ids


class Fabric:
    """The few Fabric REST calls verify needs, as the signed-in identity."""

    def __init__(self):
        token = AzureCliCredential().get_token("https://api.fabric.microsoft.com/.default").token
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"

    def items(self, ws):
        url, out = f"{API}/workspaces/{ws}/items", []
        while url:                                          # the list is paged
            r = self.s.get(url)
            r.raise_for_status()
            body = r.json()
            out += body.get("value", [])
            url = body.get("continuationUri")
        return out

    def definition(self, ws, item_id):
        r = self.s.post(f"{API}/workspaces/{ws}/items/{item_id}/getDefinition")
        if r.status_code == 202:                            # long-running: poll the operation, then read its result
            op = r.headers["Location"]
            while True:
                time.sleep(int(r.headers.get("Retry-After", 2)))
                r = self.s.get(op)
                r.raise_for_status()
                if r.json().get("status") in ("Succeeded", "Failed"):
                    break
            if r.json()["status"] == "Failed":
                raise RuntimeError(f"getDefinition failed for {item_id}: {r.text[:300]}")
            r = self.s.get(op.rstrip("/") + "/result")
        r.raise_for_status()
        parts = r.json()["definition"]["parts"]
        return {p["path"]: base64.b64decode(p["payload"]).decode("utf-8", errors="replace") for p in parts}


def main():
    ws = os.environ["WORKSPACE_ID"]
    fabric = Fabric()
    items = fabric.items(ws)
    lakehouses = [i["id"] for i in items if i["type"] == "Lakehouse" and i["displayName"] == "Ops_Lakehouse"]
    if len(lakehouses) != 1:
        sys.exit(f"expected one Ops_Lakehouse in {ws}, found {len(lakehouses)}")
    target_lh, leftovers = lakehouses[0].lower(), dev_ids(ROOT / "fabric") - {ws.lower()}
    problems = []
    for nb in (i for i in items if i["type"] == "Notebook"):
        parts = fabric.definition(ws, nb["id"])
        content = next((t for p, t in parts.items() if p.startswith("notebook-content")), "")
        lh, lh_ws = binding(content) if content else (None, None)
        if lh is not None and (lh.lower(), (lh_ws or "").lower()) != (target_lh, ws.lower()):
            problems.append(f"{nb['displayName']}: bound to lakehouse {lh} in workspace {lh_ws}")
        found = sorted(i for i in leftovers - {target_lh} if any(i in t.lower() for t in parts.values()))
        if found:
            problems.append(f"{nb['displayName']}: Dev IDs left in its definition: {found}")
        print(f"{nb['displayName']:24} lakehouse {lh or '(none)'}")
    for p in problems:
        print("PROBLEM", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
