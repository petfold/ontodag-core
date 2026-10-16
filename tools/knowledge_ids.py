"""The knowledge id of every built store: the Swarm reference of its
canonical `.od` text (ontodag.knowledge; ontodag's PACKS.md §15).

    python3 tools/knowledge_ids.py      # writes build/knowledge-ids.tsv

step7 writes each file canonical, so a file is its own canonical text and
its id is the reference of the file as it is; the tool checks that before
writing the id. These are the ids `odag publish` will print and
`merge knowledge:ID` will fetch once a version ships.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "ontodag" / "src"))
from ontodag import knowledge, native             # noqa: E402

rows = []
for path in [ROOT / "build/core.od"] + sorted((ROOT / "packs").glob("*/build/*.od")):
    text = path.read_text(encoding="utf-8")
    dag = native.loads(text, source=str(path))
    if native.dumps(dag) != text:
        sys.exit(f"{path}: not its own canonical text; run tools/step7.py first")
    name = "core" if path.name == "core.od" else path.stem
    rows.append(f"{name}\t{knowledge.knowledge_id(dag)}")
(ROOT / "build/knowledge-ids.tsv").write_text("store\tknowledge_id\n" + "\n".join(rows) + "\n")
print("\n".join(rows))
