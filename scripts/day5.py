"""
day5.py · Day 5's starter files, catch-up, reset and environment check.
PURPOSE  Day 4's catch-up replaces whole files. On Day 5 that would overwrite the files under fabric/, whose IDs
         belong to your own Dev workspace. This script catches up everything else, and inside fabric/ it changes
         only the code Day 5 adds: the gate notebook's rules() cell and Day 5's measures.
PSEUDOCODE
  start          copy the files from checkpoint/5-0 that you don't have yet; commit
  catch-up N     source = checkpoint/5-N
                 restore every file outside the item folders from the source (not your cheat sheet or gotchas log);
                 files you added that the checkpoint doesn't have are left alone
                 gate notebook: replace only the code of the cell that defines rules()
                 semantic model: add or replace only Day 5's measures, in the table file that holds them
                 an item folder you don't have at all: copy the reference one (the Part 1 fallback)
                 commit
  reset-fabric   remove item folders that are still the reference copies; commit
  doctor         check Java, pyspark, the Azure CLI and Node, and say how to fix what's missing
NOTE     Run it from the checkpoint you want, so it is always that checkpoint's version:
         git show origin/checkpoint/5-4:scripts/day5.py | python3 - catch-up 5-4
         It never touches .platform files, # META lines, or anything Fabric wrote except those two kinds of code.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ITEM = re.compile(r"^fabric/[^/]+\.(Notebook|Lakehouse|SemanticModel)/")
KEEP = {"cheat-sheet.md", "docs/copilot-gotchas.md"}
STARTER = ("scripts/day5.py", "tests/fabric/", "docs/measures.md", "deploy/",
           ".github/workflows/deploy.yml", ".github/ISSUE_TEMPLATE/deploy-params.md")
DAY5_MEASURES = ("Square Feet per Run Hour",)
CELL, METADATA = "# CELL ********************", "# METADATA ********************"


def git(*args, binary=False):
    """Run git in the current repo; stop with its message if it fails."""
    r = subprocess.run(["git", *args], capture_output=True, check=False)
    if r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr.decode(errors='replace')}")
    return r.stdout if binary else r.stdout.decode()


def checkpoint(n):
    """The ref for checkpoint/5-N: the remote branch if you have it, else a local branch."""
    n = n.split("-")[-1]
    for ref in (f"origin/checkpoint/5-{n}", f"checkpoint/5-{n}"):
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref], capture_output=True, check=False).returncode == 0:
            return ref
    sys.exit(f"checkpoint/5-{n} not found: run git fetch (or see 'Fall behind?' in the guide)")


def files_at(ref):
    return git("ls-tree", "-r", "--name-only", ref).splitlines()


def show(ref, path):
    return git("show", f"{ref}:{path}", binary=True)


def write(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def commit(message):
    git("add", "-A")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], check=False).returncode:
        git("commit", "-q", "-m", message)
        print(f"committed: {message}. Now push, then Update all in Fabric if fabric/ changed.")
    else:
        print("nothing to change: you're already there")


def start():
    """Copy checkpoint/5-0's starter files that you don't have yet."""
    src, added = checkpoint("0"), []
    for path in files_at(src):
        if path.startswith(STARTER) and not Path(path).exists():
            write(path, show(src, path))
            added.append(path)
    if added:
        print("added:", *added, sep="\n  ")
    else:
        print("all starter files are already here")
    commit("Day 5 starter files")


def cells(text):
    """[(start, end)] character spans of each cell's code in a notebook-content.py."""
    spans, pos = [], 0
    while (i := text.find(CELL, pos)) != -1:
        begin = i + len(CELL)
        end = text.find(METADATA, begin)
        end = len(text) if end == -1 else end
        spans.append((begin, end))
        pos = end
    return spans


def splice_rules_cell(local, source):
    """local notebook text with the code of its rules() cell replaced by the source's."""
    def rules_span(text):
        return next(s for s in cells(text) if "def rules(" in text[s[0]:s[1]])
    (a, b), (c, d) = rules_span(local), rules_span(source)
    return local[:a] + source[c:d] + local[b:]


def measure_span(lines, name):
    """(first, last+1) line indexes of a measure block, its /// description lines included, or None."""
    head = re.compile(rf"^\tmeasure\s+'?{re.escape(name)}'?\s*=")
    for i, line in enumerate(lines):
        if head.match(line):
            first = i
            while first > 0 and lines[first - 1].startswith("\t///"):
                first -= 1
            last = i + 1
            while last < len(lines) and lines[last].startswith("\t\t"):
                last += 1
            return first, last
    return None


def splice_measure(local, source, name):
    """local TMDL text with the named measure replaced by, or added from, the source's."""
    src, loc = source.splitlines(), local.splitlines()
    span = measure_span(src, name)
    if span is None:
        return local
    block = src[span[0]:span[1]]
    have = measure_span(loc, name)
    if have:
        loc[have[0]:have[1]] = block
    else:                                    # after the table's last measure, else before its first column
        ends = [measure_span(loc, m)[1] for m in re.findall(r"^\tmeasure\s+'?([^'=]+?)'?\s*=", local, re.MULTILINE)]
        at = max(ends) if ends else next(i for i, x in enumerate(loc) if re.match(r"^\t(column|partition)\b", x))
        loc[at:at] = [""] + block if ends else block + [""]
    return "\n".join(loc) + ("\n" if local.endswith("\n") else "")


def catch_up(n):
    src = checkpoint(n)
    src_files = set(files_at(src))
    outside = sorted(p for p in src_files if not ITEM.match(p) and p not in KEEP)
    for i in range(0, len(outside), 200):
        git("restore", f"--source={src}", "--staged", "--worktree", "--", *outside[i:i + 200])
    folders = sorted({ITEM.match(p).group(0) for p in src_files if ITEM.match(p)})
    for folder in folders:
        mine = Path(folder)
        if not mine.exists():                         # Part 1 fallback: no Fabric connection yet
            for p in src_files:
                if p.startswith(folder):
                    write(p, show(src, p))
            print(f"copied the reference {folder[7:-1]}")
        elif folder.endswith(".Notebook/"):
            nb = folder + "notebook-content.py"
            if nb in src_files and Path(nb).exists():
                text = Path(nb).read_text(encoding="utf-8")
                new = splice_rules_cell(text, show(src, nb).decode("utf-8"))
                if new != text:
                    Path(nb).write_text(new, encoding="utf-8")
                    print(f"replaced the rules() cell in {nb}")
        elif folder.endswith(".SemanticModel/"):
            for p in sorted(src_files):
                if p.startswith(folder + "definition/tables/") and Path(p).exists():
                    text = Path(p).read_text(encoding="utf-8")
                    new = text
                    for name in DAY5_MEASURES:
                        new = splice_measure(new, show(src, p).decode("utf-8"), name)
                    if new != text:
                        Path(p).write_text(new, encoding="utf-8")
                        print(f"updated Day 5's measures in {p}")
    commit(f"Catch up to {src.split('/', 1)[-1] if src.startswith('origin/') else src}")


def reset_fabric():
    """Remove item folders that are byte for byte the reference copies from checkpoint/5-1."""
    ref = checkpoint("1")
    for path in files_at(ref):
        same = path.endswith("/.platform") and ITEM.match(path) and Path(path).exists() \
            and Path(path).read_bytes() == show(ref, path)
        if same:
            shutil.rmtree(Path(path).parent)
            print(f"removed the reference {Path(path).parent}")
    commit("Remove the reference Fabric items")


def doctor():
    def version(cmd):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return (r.stdout + r.stderr).strip().splitlines()[0] if r.returncode == 0 else None
        except FileNotFoundError:
            return None
    rebuild = "rebuild the Codespace (Command Palette > Codespaces: Rebuild Container)"
    checks = [
        ("Java 17 or later", version(["java", "-version"]), rebuild),
        ("pyspark 4.1", version([sys.executable, "-c", "import pyspark; print('pyspark', pyspark.__version__)"]),
         "pip install -r requirements-dev.txt"),
        ("Azure CLI", version(["az", "version", "--output", "tsv"]), rebuild),
        ("Node 22 or later", version(["node", "--version"]), rebuild),
    ]
    for name, found, fix in checks:
        print(f"{'OK     ' if found else 'MISSING'} {name:18} {found or 'fix: ' + fix}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["start"]:
        start()
    elif args[:1] == ["catch-up"] and len(args) == 2:
        catch_up(args[1])
    elif args[:1] == ["reset-fabric"]:
        reset_fabric()
    elif args[:1] == ["doctor"]:
        doctor()
    else:
        sys.exit(__doc__)
