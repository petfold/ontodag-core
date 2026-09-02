"""docs/img/core.html — the pack as one pan-and-zoom page: the top picture and
the whole graph (radial), nodes coloured by branch, a search box, and a panel
showing a node's parents and children.  Regenerate after build.sh:

    python3 tools/picture.py
    dot   -Tsvg docs/img/top.dot -o docs/img/top.svg
    twopi -Tsvg -Granksep=2.4 -Goverlap=false -Gsplines=line docs/img/core.dot -o docs/img/core.svg
    python3 tools/atlas.py
"""
import json
import re
import shlex
from pathlib import Path
from picture import BRANCH_COLOURS, load, cones, branches_of

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "docs/img"

par, ch = load()
roots = sorted(n for n, ps in par.items() if not ps)
size, up = cones(par, ch), branches_of(par, roots)
data = {n: {"p": sorted(par[n]), "c": sorted(ch[n], key=lambda c: -size(c)), "n": size(n)} for n in par}
edges = sum(len(v) for v in par.values())


def svg_body(path):
    s = path.read_text()
    s = s[s.index("<svg"):]
    s = re.sub(r'\s(width|height)="[^"]*"', "", s, count=2)          # let CSS size it
    return s


top_svg, core_svg = svg_body(IMG / "top.svg"), svg_body(IMG / "core.svg")
legend = "".join(
    f'<button class="chip" data-branch="{r}"><i style="background:{BRANCH_COLOURS[r]}"></i>{r}<b>{size(r)}</b></button>'
    for r in sorted(roots, key=lambda r: -size(r)))

JS = r'''<script>
const DATA = __DATA__;
const ROOTS = __ROOTS__;
const names = Object.keys(DATA).sort();
document.getElementById("names").innerHTML = names.map(n => `<option value="${n}">`).join("");
const svgs = { top: document.getElementById("svg-top"), all: document.getElementById("svg-all") };
// viewBox pan-and-zoom: no library, works from a file:// open of the repo too
class PanZoom {
  constructor(svg) {
    this.svg = svg; const vb = svg.getAttribute("viewBox").split(/[ ,]+/).map(Number);
    this.home = { x: vb[0], y: vb[1], w: vb[2], h: vb[3] }; this.vb = { ...this.home };
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    let drag = null;
    svg.addEventListener("pointerdown", e => { drag = { x: e.clientX, y: e.clientY, vb: { ...this.vb } }; svg.setPointerCapture(e.pointerId); });
    svg.addEventListener("pointermove", e => { if (!drag) return; const k = this.unitsPerPixel();
      this.set({ ...drag.vb, x: drag.vb.x - (e.clientX - drag.x) * k, y: drag.vb.y - (e.clientY - drag.y) * k }); });
    svg.addEventListener("pointerup", () => drag = null); svg.addEventListener("pointercancel", () => drag = null);
    svg.addEventListener("wheel", e => { e.preventDefault(); const f = Math.exp(-e.deltaY * 0.0015); this.zoomAt(this.toSvg(e.clientX, e.clientY), f); }, { passive: false });
  }
  unitsPerPixel() { const r = this.svg.getBoundingClientRect(); return Math.max(this.vb.w / r.width, this.vb.h / r.height); }
  toSvg(cx, cy) { const r = this.svg.getBoundingClientRect(), k = this.unitsPerPixel();
    const w = r.width * k, h = r.height * k;                      // visible box, centred on vb (meet)
    return { x: this.vb.x + (this.vb.w - w) / 2 + (cx - r.left) * k, y: this.vb.y + (this.vb.h - h) / 2 + (cy - r.top) * k }; }
  set(vb) { const zoom = this.home.w / vb.w; if (zoom < 0.5 || zoom > 60) return; this.vb = vb;
    this.svg.setAttribute("viewBox", `${vb.x} ${vb.y} ${vb.w} ${vb.h}`); }
  zoomAt(p, f) { const v = this.vb; this.set({ x: p.x - (p.x - v.x) / f, y: p.y - (p.y - v.y) / f, w: v.w / f, h: v.h / f }); }
  fit() { this.set({ ...this.home }); }
  centerOn(cx, cy, zoom) { const w = this.home.w / zoom, h = this.home.h / zoom; this.set({ x: cx - w / 2, y: cy - h / 2, w, h }); }
  zoom() { return this.home.w / this.vb.w; }
}
const pz = {}; const ensure = w => pz[w] || (pz[w] = new PanZoom(svgs[w]));
let current = "top";
function show(which) {
  current = which;
  for (const k in svgs) svgs[k].classList.toggle("on", k === which);
  document.getElementById("view-top").setAttribute("aria-pressed", which === "top");
  document.getElementById("view-all").setAttribute("aria-pressed", which === "all");
  ensure(which).fit();
}
document.getElementById("view-top").onclick = () => show("top");
document.getElementById("view-all").onclick = () => show("all");
document.getElementById("fit").onclick = () => ensure(current).fit();
function nodeEl(svg, name) {
  for (const g of svg.querySelectorAll("g.node")) if (g.querySelector("title").textContent === name) return g;
  return null;
}
function highlight(name) {
  for (const svg of Object.values(svgs)) for (const g of svg.querySelectorAll("g.node.hit")) g.classList.remove("hit");
  for (const svg of Object.values(svgs)) { const g = nodeEl(svg, name); if (g) g.classList.add("hit"); }
}
function goto(name, zoom) {
  if (!DATA[name]) return;
  if (!nodeEl(svgs[current], name)) show("all");
  const svg = svgs[current], g = nodeEl(svg, name), inst = ensure(current);
  highlight(name); describe(name);
  if (!g) return;
  // Graphviz draws inside a translated <g>: map the shape's centre into viewBox space
  const shape = g.querySelector("path, polygon, ellipse"), bb = shape.getBBox();
  let pt = svg.createSVGPoint(); pt.x = bb.x + bb.width / 2; pt.y = bb.y + bb.height / 2;
  pt = pt.matrixTransform(shape.getScreenCTM()).matrixTransform(svg.getScreenCTM().inverse());
  inst.centerOn(pt.x, pt.y, zoom || Math.max(inst.zoom(), current === "all" ? 6 : 1.5));
}
function describe(name) {
  const d = DATA[name]; if (!d) return;
  const list = (arr, empty) => arr.length ? `<ul>${arr.map(n => `<li><button data-go="${n}">${n}</button></li>`).join("")}</ul>` : `<p class="empty">${empty}</p>`;
  document.getElementById("node").innerHTML = `<h2>Category</h2><h3>${name}</h3><div class="n">${d.n.toLocaleString()} below · ${d.p.length} parent${d.p.length === 1 ? "" : "s"} · ${d.c.length} child${d.c.length === 1 ? "" : "ren"}</div>
    <h2>Parents</h2>${list(d.p, ROOTS.includes(name) ? "a root branch" : "—")}
    <h2>Children</h2>${list(d.c.slice(0, 60), "none")}${d.c.length > 60 ? `<p class="empty">… and ${d.c.length - 60} more</p>` : ""}`;
}
document.getElementById("node").addEventListener("click", e => { const b = e.target.closest("[data-go]"); if (b) goto(b.dataset.go); });
for (const svg of Object.values(svgs)) svg.addEventListener("click", e => { const g = e.target.closest("g.node"); if (g) { const n = g.querySelector("title").textContent; highlight(n); describe(n); } });
document.getElementById("q").addEventListener("change", e => goto(e.target.value.trim()));
document.querySelectorAll(".chip").forEach(b => b.onclick = () => {
  const br = b.dataset.branch, on = b.getAttribute("aria-pressed") === "true";
  document.querySelectorAll(".chip").forEach(x => x.setAttribute("aria-pressed", "false"));
  const svg = svgs[current];
  svg.querySelectorAll("g.node, g.edge").forEach(g => g.classList.remove("dim"));
  if (on) return;
  b.setAttribute("aria-pressed", "true");
  const inBranch = new Set(); const stack = [br];
  while (stack.length) { const x = stack.pop(); if (inBranch.has(x)) continue; inBranch.add(x); for (const c of DATA[x].c) stack.push(c); }
  svg.querySelectorAll("g.node").forEach(g => { if (!inBranch.has(g.querySelector("title").textContent)) g.classList.add("dim"); });
  svg.querySelectorAll("g.edge").forEach(g => { const t = g.querySelector("title").textContent.split("->").map(s => s.trim()); if (!(inBranch.has(t[0]) && inBranch.has(t[1]))) g.classList.add("dim"); });
  goto(br, current === "all" ? 2 : 1.5);
});
show("top");
</script>'''.replace('__DATA__', json.dumps(data, separators=(",", ":"))).replace('__ROOTS__', json.dumps(roots))

html = f'''<title>Core Pack Atlas</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono&display=swap">
<style>
:root {{ --bg:#f4f2ee; --panel:#ffffff; --ink:#2b2822; --muted:#6f685d; --line:#d9d3c8; --accent:#8b5a2b; --hit:#c8402a; --map:#fbfaf7; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#1d1b18; --panel:#26231f; --ink:#ebe6dc; --muted:#a39a8b; --line:#3a352e; --accent:#d9a066; --hit:#ff7a5c; --map:#fbfaf7; }} }}
:root[data-theme="dark"] {{ --bg:#1d1b18; --panel:#26231f; --ink:#ebe6dc; --muted:#a39a8b; --line:#3a352e; --accent:#d9a066; --hit:#ff7a5c; --map:#fbfaf7; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:14px/1.45 "IBM Plex Sans", system-ui, sans-serif; height:100vh; display:grid; grid-template-rows:auto 1fr; }}
header {{ display:flex; flex-wrap:wrap; gap:10px 18px; align-items:baseline; padding:12px 18px 10px; border-bottom:1px solid var(--line); }}
h1 {{ font:600 22px/1.1 "Source Serif 4", Georgia, serif; margin:0; letter-spacing:-0.01em; }}
header .meta {{ color:var(--muted); font-variant-numeric:tabular-nums; }}
header .meta b {{ color:var(--ink); font-weight:500; }}
.controls {{ display:flex; gap:8px; align-items:center; margin-left:auto; flex-wrap:wrap; }}
input[type=search] {{ font:inherit; padding:6px 10px; border:1px solid var(--line); border-radius:6px; background:var(--panel); color:var(--ink); width:16rem; }}
input[type=search]:focus, button:focus-visible {{ outline:2px solid var(--accent); outline-offset:1px; }}
button {{ font:inherit; padding:6px 10px; border:1px solid var(--line); border-radius:6px; background:var(--panel); color:var(--ink); cursor:pointer; }}
button[aria-pressed="true"] {{ border-color:var(--accent); color:var(--accent); }}
main {{ display:grid; grid-template-columns:1fr minmax(240px, 300px); min-height:0; }}
#stage {{ position:relative; background:var(--map); border-right:1px solid var(--line); overflow:hidden; }}
#stage svg {{ position:absolute; inset:0; width:100%; height:100%; display:none; }}
#stage svg.on {{ display:block; }}
#stage .hint {{ position:absolute; left:12px; bottom:10px; color:#6f685d; font-size:12px; background:rgba(255,255,255,.75); padding:3px 8px; border-radius:4px; pointer-events:none; }}
g.node {{ cursor:pointer; }}
g.node.hit path, g.node.hit polygon {{ stroke:var(--hit); stroke-width:3px; }}
g.node.dim {{ opacity:.18; }} g.edge.dim {{ opacity:.08; }}
aside {{ overflow:auto; padding:14px 16px; display:flex; flex-direction:column; gap:14px; }}
aside h2 {{ font:500 11px/1 "IBM Plex Sans", sans-serif; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 0 8px; }}
.legend {{ display:flex; flex-direction:column; gap:4px; }}
.chip {{ display:flex; align-items:center; gap:8px; padding:4px 8px; text-align:left; }}
.chip i {{ width:12px; height:12px; border-radius:3px; border:1px solid #8a7f70; flex:none; }}
.chip b {{ margin-left:auto; font-weight:400; color:var(--muted); font-variant-numeric:tabular-nums; }}
#node h3 {{ font:600 20px/1.15 "Source Serif 4", Georgia, serif; margin:0 0 2px; word-break:break-word; }}
#node .n {{ color:var(--muted); margin-bottom:10px; }}
#node ul {{ list-style:none; margin:0 0 10px; padding:0; display:flex; flex-wrap:wrap; gap:4px; }}
#node li button {{ padding:2px 7px; font-size:13px; font-family:"IBM Plex Mono", monospace; }}
#node p.empty {{ color:var(--muted); }}
@media (max-width: 720px) {{ main {{ grid-template-columns:1fr; grid-template-rows:1fr auto; }} #stage {{ border-right:0; border-bottom:1px solid var(--line); }} aside {{ max-height:40vh; }} }}
</style>
<header>
  <h1>Core Pack Atlas</h1>
  <span class="meta"><b>{len(par):,}</b> categories · <b>{edges:,}</b> edges · <b>{len(roots)}</b> branches · core v2</span>
  <div class="controls">
    <button id="view-top" aria-pressed="true">Top</button>
    <button id="view-all" aria-pressed="false">Everything</button>
    <button id="fit">Fit</button>
    <input id="q" type="search" placeholder="Find a category…" list="names" autocomplete="off">
    <datalist id="names"></datalist>
  </div>
</header>
<main>
  <div id="stage">
    {top_svg.replace('<svg', '<svg id="svg-top" class="on"', 1)}
    {core_svg.replace('<svg', '<svg id="svg-all"', 1)}
    <div class="hint">drag to pan · wheel to zoom · click a category</div>
  </div>
  <aside>
    <section><h2>Branches</h2><div class="legend">{legend}</div></section>
    <section id="node"><h2>Category</h2><p class="empty">Click a category on the map, or find one above. Parents and children are listed here; click one to move to it.</p></section>
  </aside>
</main>
''' + JS + '''
'''
(IMG / "core.html").write_text(html)
print("core.html", len(html) // 1024, "KB")
