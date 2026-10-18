#!/usr/bin/env python3
"""Builds the animated terminal-style SVG assets used by README.md.

Pure SVG/SMIL (GitHub strips JS/CSS from READMEs). Terminal / neofetch look in a
GitHub-dark palette. The hypercubes are real 4D / 5D rotations projected to 2D
and baked into animation keyframes.
Run:  python3 .github/scripts/build_assets.py
"""
import itertools, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "assets")
os.makedirs(OUT, exist_ok=True)

BG, PANEL, BAR, LINE = "#0d1117", "#0d1117", "#161b22", "#30363d"
TXT, MUTED, DIM = "#e6edf3", "#8b949e", "#6e7681"
GREEN, CYAN, PURPLE, ORANGE, YEL, RED = "#3fb950", "#58a6ff", "#bc8cff", "#f78166", "#d29922", "#ff7b72"
MONO = "'Fira Code','JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
W = 1200


def n(x):
    s = f"{x:.1f}"
    if s in ("-0.0", "0.0"):
        return "0"
    return s[:-2] if s.endswith(".0") else s


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def write(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"{name:18s} {len(svg)/1024:7.1f} KB")


def anim(attr, vals, dur):
    return f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" values="{";".join(vals)}"/>'


# ---------------------------------------------------------------- n-D math
def rot(v, i, j, a):
    v = list(v)
    c, s = math.cos(a), math.sin(a)
    v[i], v[j] = v[i] * c - v[j] * s, v[i] * s + v[j] * c
    return v


def project(v, cam, d=4.0):
    v = list(v)
    while len(v) > 3:
        w = v.pop()
        k = cam / (cam - w)
        v = [c * k for c in v]
    x, y, z = v
    k = d / (d + z)
    return x * k, y * k, k


def hypercube(dim):
    verts = list(itertools.product([-1, 1], repeat=dim))
    edges = []
    for a in range(len(verts)):
        for b in range(a + 1, len(verts)):
            diff = [i for i in range(dim) if verts[a][i] != verts[b][i]]
            if len(diff) == 1:
                edges.append((a, b, diff[0]))
    return verts, edges


def wire(dim, planes, cx, cy, S, cam, N, dur, base_col, extra_cols, dot_col, sw=1.7, fade_in=None):
    verts, edges = hypercube(dim)
    groups = {}
    vx = [[] for _ in verts]; vy = [[] for _ in verts]; vr = [[] for _ in verts]
    for k in range(N + 1):
        t = 2 * math.pi * k / N
        Q = []
        for v in verts:
            p = [q / math.sqrt(dim) for q in v]
            for (i, j, m, ph) in planes:
                p = rot(p, i, j, m * t + ph)
            x, y, kk = project(p, cam)
            Q.append((cx + x * S, cy + y * S, kk))
        for key in (0, *range(3, dim)):
            sel = [e for e in edges if (e[2] < 3) == (key == 0) and (key == 0 or e[2] == key)]
            groups.setdefault(key, []).append("".join(f"M{n(Q[a][0])} {n(Q[a][1])}L{n(Q[b][0])} {n(Q[b][1])}" for a, b, d in sel))
        for i, q in enumerate(Q):
            vx[i].append(n(q[0])); vy[i].append(n(q[1])); vr[i].append(n(max(1.6, 3.6 * q[2] ** 2)))
    out = ""
    for key, vals in groups.items():
        col = base_col if key == 0 else extra_cols[key - 3]
        out += f'<path fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round">{anim("d", vals, dur)}</path>'
    for i in range(len(verts)):
        out += f'<circle fill="{dot_col}">{anim("cx", vx[i], dur)}{anim("cy", vy[i], dur)}{anim("r", vr[i], dur)}</circle>'
    if fade_in is not None:
        return (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".8s" begin="{fade_in}s" fill="freeze"/>{out}</g>')
    return out


# ---------------------------------------------------------- typing engine
class Typer:
    """Typewriter lines: per-character stepped clip + a block cursor that follows."""

    def __init__(self):
        self.defs, self.body, self.i = "", "", 0

    def line(self, x, y, segs, fs, t0, cps=32, keep_cursor=False, cur_col=GREEN):
        self.i += 1
        cid = f"c{self.i}"
        chars = sum(len(s) for s, _ in segs)
        cw = fs * .6
        dur = max(chars / cps, .05)
        steps = [n(i * cw) for i in range(chars + 1)]
        xs = [n(x + i * cw) for i in range(chars + 1)]
        self.defs += (f'<clipPath id="{cid}"><rect x="{x}" y="{n(y-fs)}" height="{n(fs*1.5)}" width="0">'
                      f'<animate attributeName="width" dur="{dur:.2f}s" begin="{t0:.2f}s" fill="freeze" calcMode="discrete" values="{";".join(steps)}"/></rect></clipPath>')
        spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in segs)
        self.body += (f'<g clip-path="url(#{cid})"><text xml:space="preserve" x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}" '
                      f'textLength="{n(chars*cw)}" lengthAdjust="spacing">{spans}</text></g>')
        cur = (f'<rect y="{n(y-fs*.85)}" width="{n(cw*.9)}" height="{n(fs*1.15)}" fill="{cur_col}" opacity="0">'
               f'<set attributeName="opacity" to="1" begin="{t0:.2f}s" fill="freeze"/>'
               f'<animate attributeName="x" dur="{dur:.2f}s" begin="{t0:.2f}s" fill="freeze" calcMode="discrete" values="{";".join(xs)}"/>')
        if keep_cursor:
            cur += (f'<animate attributeName="opacity" begin="{t0+dur:.2f}s" dur="1.1s" repeatCount="indefinite" values="1;1;0;0" keyTimes="0;.5;.5;1"/>')
        else:
            cur += f'<set attributeName="opacity" to="0" begin="{t0+dur:.2f}s" fill="freeze"/>'
        cur += '</rect>'
        self.body += cur
        return t0 + dur

    def out(self):
        return self.defs, self.body


def prompt_segs(cmd, path="~"):
    return [("pratham@shrestha", GREEN), (":", TXT), (path, CYAN), ("$ ", TXT), (cmd, TXT)]


def window(x, y, w, h, title):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
            f'<path d="M{x} {y+44} V{y+12} Q{x} {y} {x+12} {y} H{x+w-12} Q{x+w} {y} {x+w} {y+12} V{y+44}Z" fill="{BAR}"/>'
            f'<line x1="{x}" x2="{x+w}" y1="{y+44}" y2="{y+44}" stroke="{LINE}"/>'
            f'<circle cx="{x+26}" cy="{y+22}" r="6.5" fill="#ff5f56"/><circle cx="{x+48}" cy="{y+22}" r="6.5" fill="#ffbd2e"/><circle cx="{x+70}" cy="{y+22}" r="6.5" fill="#27c93f"/>'
            f'<text x="{x+w/2}" y="{y+27}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">{esc(title)}</text>')


def doc(h, body, defs="", label=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{esc(label)}">'
            f'<defs>{defs}</defs>{body}</svg>')


def reveal(inner, delay, dy=10, dur=.6):
    return (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="{dur}s" begin="{delay}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 {dy}" to="0 0" dur="{dur}s" begin="{delay}s" fill="freeze"/>{inner}</g>')


# ------------------------------------------------------------------ HEADER
def header():
    H = 480
    t = Typer()
    end = t.line(64, 108, prompt_segs("git fetch"), 20, .4, cps=22)
    end = t.line(64, 142, [("Fetching . . .", DIM)], 14, end + .25, cps=14)
    rows = [("Name", "Pratham Shrestha"), ("Role", "Full-Stack Developer"), ("Based", "Kathmandu, Nepal"),
            ("Now", "Frontend Developer @ Prixa"), ("Stack", "React · Next.js · TypeScript · Node.js"), ("Mood", "Delusional")]
    t0 = end + .3
    t0 = t.line(520, 200, [("pratham", GREEN), ("@", TXT), ("shrestha", GREEN)], 24, t0, cps=26)
    t0 = t.line(520, 218, [("─" * 16, DIM)], 14, t0 + .02, cps=120)
    for i, (k, v) in enumerate(rows):
        t0 = t.line(520, 262 + i * 32, [(k.ljust(7), CYAN), (": ", DIM), (v, TXT)], 19, t0 + .05, cps=70)
    defs, body = t.out()
    swatches = "".join(f'<rect x="{520+i*34}" y="438" width="28" height="14" rx="3" fill="{c}"/>'
                       for i, c in enumerate([RED, ORANGE, YEL, GREEN, CYAN, PURPLE, TXT, DIM]))
    logo = wire(4, [(0, 3, 1, 0), (1, 3, 2, 0), (0, 2, 1, .4), (1, 2, 2, 0)], 270, 290, 118, 2.6, 120, 24,
                CYAN, [GREEN], TXT, sw=2, fade_in=2.2)
    svg = doc(H, f'<rect width="{W}" height="{H}" fill="{BG}" rx="0"/>' + window(24, 20, 1152, 440, "pratham@shrestha: ~") + body + logo +
              reveal(swatches, t0 + .1), defs, "Terminal: git fetch for Pratham Shrestha, Full-Stack Developer from Nepal")
    write("header.svg", svg)


# ----------------------------------------------------------- SECTION PROMPTS
def prompt(slug, cmd, path):
    t = Typer()
    t.line(28, 42, prompt_segs(cmd, path), 20, .3, cps=24, keep_cursor=True)
    defs, body = t.out()
    write(f"prompt-{slug}.svg", doc(64, f'<rect width="{W}" height="64" fill="{BG}"/>{body}', defs, f"$ {cmd}"))


# -------------------------------------------------------------- PROJECTS
PROJECTS = [
    ("inmark-ai", "Next.js · Tiptap · Motion · Claude", "inmark.ai"),
    ("sports-web", "live on Vercel", "sports-web-two-orcin.vercel.app"),
    ("sunrise-dental", "live on Vercel", "sunrise-dental-ashy.vercel.app"),
    ("blackfire-studio", "live on Vercel", "blackfire-studio.vercel.app"),
    ("e-commerce", "React · Tailwind · GSAP", "e-commerce-omega-taupe-84.vercel.app"),
]


def projects():
    H = 70 + 44 * len(PROJECTS) + 40
    out = f'<text x="28" y="64" font-family="{MONO}" font-size="14" fill="{DIM}">total {len(PROJECTS)}</text>'
    for i, (name, stack, dom) in enumerate(PROJECTS):
        y = 104 + i * 44
        row = (f'<text x="28" y="{y}" font-family="{MONO}" font-size="16" fill="{DIM}">drwxr-xr-x</text>'
               f'<text x="190" y="{y}" font-family="{MONO}" font-size="19" font-weight="700" fill="{CYAN}">{name}/</text>'
               f'<text x="450" y="{y}" font-family="{MONO}" font-size="16" fill="{MUTED}">{esc(stack)}</text>'
               f'<text x="800" y="{y}" font-family="{MONO}" font-size="16" fill="{GREEN}">↗ {esc(dom)}</text>')
        out += reveal(row, .4 + i * .18, 8, .5)
    write("projects.svg", doc(H, f'<rect width="{W}" height="{H}" fill="{BG}"/>' + out, label="Projects: inmark-ai, sports-web, sunrise-dental, blackfire-studio, e-commerce"))


# ----------------------------------------------------------------- GIT LOG
LOG = [
    ("3f2a9c1", "HEAD -> main", "Frontend Developer @ Prixa (Ting Ting)", "Apr 2026 → now"),
    ("8b41d07", "", "Frontend Developer Intern @ Black Moon Pvt. Ltd.", "Feb 2026 → Apr 2026"),
    ("c07e5a2", "", "Frontend Developer Intern @ TEDx Baneshwor", "Sep 2024 → Jan 2025"),
]


def log():
    H = 50 + 46 * len(LOG) + 30
    out = f'<line x1="41" x2="41" y1="40" y2="{50+46*(len(LOG)-1)+10}" stroke="{LINE}" stroke-width="2"/>'
    for i, (h, ref, msg, when) in enumerate(LOG):
        y = 64 + i * 46
        dot = f'<circle cx="41" cy="{y-6}" r="6" fill="{GREEN if i == 0 else PURPLE}"/>'
        if i == 0:
            dot += f'<circle cx="41" cy="{y-6}" r="6" fill="none" stroke="{GREEN}"><animate attributeName="r" values="6;14;6" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;0;.8" dur="2s" repeatCount="indefinite"/></circle>'
        tag = f'<tspan fill="{YEL}">(</tspan><tspan fill="{CYAN}">HEAD -&gt; </tspan><tspan fill="{GREEN}">main</tspan><tspan fill="{YEL}">) </tspan>' if ref else ""
        row = (dot + f'<text xml:space="preserve" x="70" y="{y}" font-family="{MONO}" font-size="18"><tspan fill="{ORANGE}">{h} </tspan>{tag}<tspan fill="{TXT}">{esc(msg)}</tspan></text>'
               f'<text x="1172" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" fill="{DIM}">{when}</text>')
        out += reveal(row, .3 + i * .25, 8, .5)
    write("log.svg", doc(H, f'<rect width="{W}" height="{H}" fill="{BG}"/>' + out, label="Experience: Prixa, Black Moon, TEDx Baneshwor"))


# ------------------------------------------------------------------ FOOTER
def footer():
    H = 190
    t = Typer()
    e = t.line(28, 50, prompt_segs('echo "thanks for visiting ✦"'), 20, .3, cps=24)
    e = t.line(28, 90, [("thanks for visiting ✦", GREEN)], 20, e + .2, cps=30)
    t.line(28, 150, prompt_segs("", "~"), 20, e + .5, cps=24, keep_cursor=True)
    defs, body = t.out()
    pent = wire(5, [(0, 3, 1, 0), (1, 4, 1, 0), (2, 3, 2, 0), (0, 2, 1, .5), (1, 2, 3, 0), (3, 4, 1, 0)], 1030, 95, 78, 3.0, 120, 26,
                MUTED, [PURPLE, CYAN], TXT, sw=1.4)
    write("footer.svg", doc(H, f'<rect width="{W}" height="{H}" fill="{BG}"/>{body}<g>{pent}</g>', defs, "Thanks for visiting"))


if __name__ == "__main__":
    header(); projects(); log(); footer()
    prompt("about", "cat about.md", "~")
    prompt("use", "stack --use", "~/stack")
    prompt("learning", "stack --learning", "~/stack")
    prompt("projects", "ls -l projects/", "~")
    prompt("log", "git log --oneline career/", "~")
    prompt("metrics", "gh metrics --live", "~")
