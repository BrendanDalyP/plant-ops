"""Tests for the measure Day 5 adds to Ops_Model, read from the TMDL files Fabric writes to Git.

PURPOSE  A measure is a definition people trust without reading it, so the file must say what docs/measures.md
         says: a ratio of sums, in the right folder, with the agreed description and format.
PSEUDOCODE
  doc   = the row for "Square Feet per Run Hour" in docs/measures.md (definition, folder, format, description)
  block = the measure's lines in fabric/Ops_Model.SemanticModel/definition/tables/fact_production.tmdl:
          its /// description lines, the "measure 'name' =" line, and its indented properties
  check the block exists (each test fails on its own until it does)
  check its expression is the doc's ratio of sums (no AVERAGEX, no SUMX)
  check its description, displayFolder and formatString match the doc
NOTE     TMDL indents with tabs: one tab for a table's measures and columns, two for their properties.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TMDL = ROOT / "fabric" / "Ops_Model.SemanticModel" / "definition" / "tables" / "fact_production.tmdl"
NAME = "Square Feet per Run Hour"


def doc_row(name):
    """{measure, table, definition, folder, format, description} for one row of docs/measures.md."""
    text = (ROOT / "docs" / "measures.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == name:
            keys = ("measure", "table", "definition", "folder", "format", "description")
            return dict(zip(keys, cells)) | {"definition": cells[2].strip("`")}
    raise AssertionError(f"docs/measures.md has no row for {name!r}")


def measure_block(text, name):
    """(description, expression, properties) of one measure in a TMDL table file, or None."""
    lines = text.splitlines()
    head = re.compile(rf"^\tmeasure\s+'?{re.escape(name)}'?\s*=\s*(.*)$")
    for i, line in enumerate(lines):
        m = head.match(line)
        if not m:
            continue
        desc, j = [], i - 1
        while j >= 0 and lines[j].startswith("\t///"):
            desc.insert(0, lines[j][4:].strip())
            j -= 1
        expr, props, k = [m.group(1).strip()], {}, i + 1
        while k < len(lines) and lines[k].startswith("\t\t"):
            prop = re.match(r"^\t\t(\w+):\s*(.*)$", lines[k])
            if prop:
                props[prop.group(1)] = prop.group(2).strip()
            else:
                expr.append(lines[k].strip())
            k += 1
        return " ".join(desc), " ".join(e for e in expr if e), props
    return None


def squash(dax):
    return re.sub(r"\s+", "", dax)


@pytest.fixture(scope="module")
def block():
    if not TMDL.exists():
        pytest.fail(f"{TMDL.relative_to(ROOT)} not found: connect your Dev workspace to this branch (Part 1)")
    return measure_block(TMDL.read_text(encoding="utf-8"), NAME)


MISSING = f"fact_production.tmdl has no measure named {NAME!r} yet"


def test_measure_is_the_documented_ratio_of_sums(block):
    assert block, MISSING
    _, expression, _ = block
    assert squash(expression) == squash(doc_row(NAME)["definition"])
    assert "AVERAGEX" not in expression.upper() and "SUMX" not in expression.upper()


def test_measure_description_matches_the_doc(block):
    assert block, MISSING
    description, _, _ = block
    assert description == doc_row(NAME)["description"]


def test_measure_folder_and_format_match_the_doc(block):
    assert block, MISSING
    _, _, props = block
    row = doc_row(NAME)
    assert props.get("displayFolder") == row["folder"]
    assert props.get("formatString") == row["format"]
