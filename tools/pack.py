"""Where a build reads and writes. The top level builds `core`; a pack
(`--pack physics`) builds on top of it in packs/<name>/, reusing the core's
concepts and alignments as the placed base it must attach to."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pack_arg(argv=None):
    argv = sys.argv if argv is None else argv
    if "--pack" in argv:
        i = argv.index("--pack")
        name = argv[i + 1]
        del argv[i:i + 2]
        return name
    return None


class Dirs:
    def __init__(self, pack=None):
        self.pack = pack
        base = ROOT / "packs" / pack if pack else ROOT
        self.align, self.views, self.build = base / "align", base / "views", base / "build"
        for d in (self.align, self.views, self.build):
            d.mkdir(parents=True, exist_ok=True)
        self.concepts = self.align / "concepts.tsv"
        self.pack_od = self.build / (f"{pack}.od" if pack else "core.od")
        # the base a pack attaches to: the core's concepts and built pack
        self.base_concepts = ROOT / "align/concepts.tsv" if pack else None
        self.base_od = ROOT / "build/core.od" if pack else None
