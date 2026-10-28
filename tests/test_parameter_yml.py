# =====================================================================================
# test_parameter_yml.py · Every Dev ID in the notebooks' metadata is replaced for TEST
# PURPOSE  A deploy that leaves one Dev lakehouse ID behind points a Test notebook at Dev data. Catch it in
#          CI, before anything is deployed.
# PSEUDOCODE
#   params   = fabric/parameter.yml; its find_replace entries for Notebook items
#   every entry has a TEST value, and matches at least one # META line (run with -s to see which)
#   for each fabric/**/notebook-content.py:
#       dev_ids  = every GUID on its META lines
#       replaced = the file after applying each entry the way fabric-cicd does (a regex entry replaces
#                  only its captured group), with a placeholder for each TEST value
#       no dev_id may be left in replaced
# =====================================================================================
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
FABRIC = ROOT / "fabric"
GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
NOTEBOOKS = sorted(FABRIC.rglob("notebook-content.py"))


def entries():
    params = yaml.safe_load((FABRIC / "parameter.yml").read_text(encoding="utf-8"))
    return [e for e in params.get("find_replace", []) if e.get("item_type", "Notebook") == "Notebook"]


def apply(text, entry):
    """Apply one find_replace entry the way fabric-cicd does, with a placeholder for the TEST value."""
    value = "<TEST:" + entry["replace_value"]["TEST"] + ">"
    if str(entry.get("is_regex", "")).lower() == "true":
        return re.sub(entry["find_value"], lambda m: m.group(0).replace(m.group(1), value), text)
    return text.replace(entry["find_value"], value)


def test_every_entry_has_a_test_value():
    assert entries(), "fabric/parameter.yml has no find_replace entries for notebooks"
    assert all("TEST" in e["replace_value"] for e in entries())


@pytest.mark.parametrize("index", range(len(entries())), ids=lambda i: f"entry-{i + 1}")
def test_every_entry_matches_a_meta_line(index):
    entry = entries()[index]
    found = [line.strip() for nb in NOTEBOOKS for line in nb.read_text(encoding="utf-8").splitlines()
             if line.startswith("# META") and re.search(entry["find_value"], line)]
    for line in found:
        print(f"entry {index + 1} matches: {line}")
    assert found, f"entry {index + 1} matches no # META line: {entry['find_value']}"


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.parent.name)
def test_no_dev_id_survives(notebook):
    text = notebook.read_text(encoding="utf-8")
    dev_ids = {g for line in text.splitlines() if line.startswith("# META") for g in re.findall(GUID, line)}
    for entry in entries():
        text = apply(text, entry)
    left = sorted(g for g in dev_ids if g in text)
    assert not left, f"{notebook.parent.name}: not replaced for TEST: {left}"
