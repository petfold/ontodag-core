"""One shape for every source: a subsumption graph of ids with labels and parents.

    Graph(nodes={id: (label, [parent_id, ...])}, root=id)

Everything downstream (tree printing, top cuts, .od export) works on this,
so a new source needs only an extractor that fills it.  Names in the exported
.od files are OntoDAG names: lower-case, hyphenated, and disambiguated with
`.2`, `.3` when two ids share a label (in id order, so stable across runs).
"""
import pickle
import re
import sys
from collections import defaultdict, deque


class Graph:
    def __init__(self, nodes, root):
        self.nodes = nodes                      # id -> (label, [parents])
        self.root = root
        self.children = defaultdict(list)
        for s, (_, ps) in nodes.items():
            for p in ps:
                self.children[p].append(s)
        self._desc = {}

    # --- measures -----------------------------------------------------------
    def label(self, s):
        return self.nodes[s][0] or s

    def parents(self, s):
        return self.nodes[s][1]

    def descendants(self, s):
        """Size of the cone below s (exclusive), memoised."""
        if s not in self._desc:
            seen, stack = set(), [s]
            while stack:
                x = stack.pop()
                for c in self.children[x]:
                    if c not in seen:
                        seen.add(c)
                        stack.append(c)
            self._desc[s] = len(seen)
        return self._desc[s]

    def depths(self):
        """Minimum depth from the root, BFS."""
        d = {self.root: 0}
        q = deque([self.root])
        while q:
            x = q.popleft()
            for c in self.children[x]:
                if c not in d:
                    d[c] = d[x] + 1
                    q.append(c)
        return d

    # --- cuts -----------------------------------------------------------------
    def top(self, depth, min_size):
        """Ids within `depth` of the root whose cone has at least `min_size`
        members.  The root itself is excluded (it becomes OntoDAG's `*`)."""
        d = self.depths()
        return {s for s, k in d.items()
                if 0 < k <= depth and self.descendants(s) >= min_size}

    def print_tree(self, depth, min_size, out=print):
        def show(s, k):
            extra = "" if len(self.parents(s)) <= 1 else f"  (+{len(self.parents(s)) - 1} parent)"
            out("  " * k + f"{self.label(s)}  [{self.descendants(s)}]{extra}")
            if k < depth:
                for c in sorted(self.children[s], key=lambda c: -self.descendants(c)):
                    if self.descendants(c) >= min_size:
                        show(c, k + 1)
        show(self.root, 0)

    # --- export -----------------------------------------------------------------
    def names(self, ids):
        """OntoDAG names for a set of ids: normalised labels, collisions
        suffixed `.2`, `.3`, ... in id order."""
        by_label = defaultdict(list)
        for s in sorted(ids):
            by_label[normalise(self.label(s))].append(s)
        out = {}
        for lab, ss in by_label.items():
            for i, s in enumerate(ss):
                out[s] = lab if i == 0 else f"{lab}.{i + 1}"
        return out

    def to_ontodag(self, ids):
        """An OntoDAG over exactly `ids`; edges kept only between included
        ids, so a node whose parents all fell outside the cut hangs from `*`."""
        from ontodag import OntoDAG
        names = self.names(ids)
        dag = OntoDAG()
        pending = {s: [p for p in self.parents(s) if p in ids] for s in ids}
        placed = set()
        while pending:
            ready = [s for s, ps in pending.items() if all(p in placed for p in ps)]
            if not ready:
                # Mutual subclass (OWL equivalence) cannot be a DAG edge pair.
                # Cut the node with the fewest unplaced parents loose from
                # them and say so; the source's cycle is the finding.
                s = min(pending, key=lambda x: (len([p for p in pending[x] if p not in placed]), x))
                dropped = [p for p in pending[s] if p not in placed]
                pending[s] = [p for p in pending[s] if p in placed]
                print(f"note: cycle broken at {names[s]!r}: dropped parents "
                      f"{[names[p] for p in dropped]}", file=sys.stderr)
                continue
            for s in sorted(ready):
                dag.put(names[s], [names[p] for p in pending.pop(s)])
                placed.add(s)
        return dag

    def write_od(self, ids, path):
        from ontodag.__main__ import FileBackend
        FileBackend(str(path)).save(self.to_ontodag(ids))

    # --- cache --------------------------------------------------------------------
    def save(self, path):
        pickle.dump((self.nodes, self.root), open(path, "wb"))

    @classmethod
    def load(cls, path):
        nodes, root = pickle.load(open(path, "rb"))
        return cls(nodes, root)


def normalise(label):
    """`Physical_entity` / `PhysicalEntity` / `physical entity` -> `physical-entity`."""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", label)      # CamelCase boundaries
    s = re.sub(r"[\s_/]+", "-", s.strip())
    s = re.sub(r"[^A-Za-z0-9.'-]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-").lower()
    return s or "unnamed"
