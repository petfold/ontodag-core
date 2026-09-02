"""Record a batch of judgements: every direct single-witness edge in the same
selection review_batch.py printed is ACCEPTED unless named in --reject
(`sub ⊑ sup: reason` lines, one per line, from a file or stdin).  Appends to
align/claude-review.tsv.  Use only after reading the batch."""
import argparse
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--branch")
ap.add_argument("--witness")
ap.add_argument("--limit", type=int, default=100)
ap.add_argument("--reject", help="file of `sub ⊑ sup: reason` lines (default stdin)")
ap.add_argument("--label", default="")
a = ap.parse_args()

cmd = [sys.executable, str(ROOT / "tools/review_batch.py"), "--limit", str(a.limit)]
if a.branch: cmd += ["--branch", a.branch]
if a.witness: cmd += ["--witness", a.witness]
batch = [l.split("  [")[0] for l in subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()
         if not l.startswith("#")]
pairs = [tuple(x.strip() for x in b.split(" ⊑ ")) for b in batch]
rejects = {}
for line in (open(a.reject) if a.reject else sys.stdin):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    edge, _, reason = line.partition(":")
    sub, _, sup = edge.partition("⊑")
    rejects[(sub.strip(), sup.strip())] = reason.strip()
unknown = set(rejects) - set(pairs)
if unknown:
    sys.exit(f"rejects not in this batch: {sorted(unknown)}")
off = {r["name"]: r["wordnet"] for r in csv.DictReader(open(ROOT / "align/concepts.tsv"), delimiter="\t")}
with open(ROOT / "align/claude-review.tsv", "a", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    fh.write(f"# --- {a.label or 'batch'}: {a.witness or 'any'} {a.branch or ''} ---\n")
    for p in pairs:
        if p in rejects:
            w.writerow([p[0], p[1], "reject", rejects[p], off.get(p[0], ""), off.get(p[1], "")])
        else:
            w.writerow([p[0], p[1], "accept", "", off.get(p[0], ""), off.get(p[1], "")])
print(f"{len(pairs) - len(rejects)} accepted, {len(rejects)} rejected")
