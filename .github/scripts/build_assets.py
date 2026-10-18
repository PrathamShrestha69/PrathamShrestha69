#!/usr/bin/env python3
"""Builds the animated SVG assets used by README.md.

Pure SVG/SMIL (GitHub strips JS/CSS from READMEs). Style follows the portfolio:
near-black, one red accent, huge tight type, thin rules, mono micro-labels.
The hypercubes are real 4D / 5D rotations projected to 2D and baked into keyframes.
Run:  python3 .github/scripts/build_assets.py
"""
import base64, itertools, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "assets")
IMG = os.path.join(HERE, "img")
os.makedirs(OUT, exist_ok=True)

BG, PANEL, LINE = "#0d0d0d", "#141414", "#3f3f46"
TXT, MUTED, DIM = "#f4f4f5", "#a1a1aa", "#71717a"
RED, RED2, RED3 = "#dc2626", "#ef4444", "#ff8a8a"
SANS = "Geist,Inter,'Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "'Geist Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
JP = "'Noto Sans JP','Hiragino Sans','Yu Gothic',Meiryo,sans-serif"
W = 1200


def n(x):
    s = f"{x:.1f}"
    if s in ("-0.0", "0.0"):
        return "0"
    return s[:-2] if s.endswith(".0") else s


def write(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"{name:20s} {len(svg)/1024:7.1f} KB")


def b64(name):
    with open(os.path.join(IMG, name), "rb") as fh:
        return "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def anim(attr, vals, dur):
    return f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" values="{";".join(vals)}"/>'


def reveal(inner, delay, dx=0, dy=0, dur=.9):
    """GSAP-style one-shot entrance: fade + slide, eased, frozen at the end."""
    sp = 'calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"'
    return (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="{dur}s" begin="{delay}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="{dx} {dy}" to="0 0" dur="{dur}s" begin="{delay}s" fill="freeze" {sp}/>'
            f'{inner}</g>')


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


def wire(dim, planes, cx, cy, S, cam, N, dur, base_col, extra_cols, dot_col, dot_stroke, sw=1.6):
    """Rotating hypercube as animated paths: base_col for the 3 spatial axes, extra_cols for the rest."""
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
            vx[i].append(n(q[0])); vy[i].append(n(q[1])); vr[i].append(n(max(1.6, 3.4 * q[2] ** 2)))
    out = ""
    for key, vals in groups.items():
        col = base_col if key == 0 else extra_cols[key - 3]
        out += f'<path fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round">{anim("d", vals, dur)}</path>'
    for i in range(len(verts)):
        out += (f'<circle fill="{dot_col}" stroke="{dot_stroke}" stroke-width="1.2">{anim("cx", vx[i], dur)}{anim("cy", vy[i], dur)}{anim("r", vr[i], dur)}</circle>')
    return out


# ------------------------------------------------------------- shared bits
def strip(y):
    """The ©Crafting - クラフト row + thin rule that repeats across the portfolio."""
    f = f'font-family="{MONO}" font-size="13" fill="{MUTED}"'
    jp = f'font-family="{MONO},{JP}" font-size="13" fill="{MUTED}"'
    return (f'<text x="48" y="{y}" {jp}>©Crafting  - クラフト</text>'
            f'<text x="600" y="{y}" text-anchor="middle" {jp}>Animating - アニメーション化する</text>'
            f'<text x="1152" y="{y}" text-anchor="end" {f}>Building</text>'
            f'<line x1="48" x2="1152" y1="{y+16}" y2="{y+16}" stroke="#d4d4d8" stroke-opacity=".55" stroke-width="1" stroke-dasharray="1104" stroke-dashoffset="1104">'
            f'<animate attributeName="stroke-dashoffset" from="1104" to="0" dur="1.1s" begin="0.1s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/></line>')


def doc(h, body, defs="", label=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{esc(label)}">'
            f'<defs>{defs}</defs><rect width="{W}" height="{h}" fill="{BG}"/>{body}</svg>')


# -------------------------------------------------------------------- HERO
def hero():
    H = 680
    img = b64("hero.jpg")
    tess = wire(4, [(0, 3, 1, 0), (1, 3, 2, 0), (0, 2, 1, .4), (1, 2, 2, 0)], 270, 420, 108, 2.6, 120, 24,
                "#ffffff", ["#0d0d0d"], "#0d0d0d", "#ffffff", sw=2)
    tag = "".join(f'<text x="48" y="{150+i*34}" font-family="{SANS}" font-size="24" letter-spacing="-.5" fill="{TXT}">{t}</text>'
                  for i, t in enumerate(["A Web Developer who designs", "and creates websites in", "React.js and Next.js"]))
    roles = "".join(f'<text x="1152" y="{150+i*38}" text-anchor="end" font-family="{SANS}" font-size="28" letter-spacing="-.8" fill="{TXT}">{t}</text>'
                    for i, t in enumerate(["Developer", "Designer", "Animator", "Delusional"]))
    status = (f'<g><circle cx="868" cy="318" r="5" fill="{RED2}"><animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/>'
              f'<animate attributeName="r" values="5;7;5" dur="1.6s" repeatCount="indefinite"/></circle>'
              f'<text x="1152" y="323" text-anchor="end" font-family="{MONO}" font-size="13" letter-spacing="1.5" fill="{TXT}">NOW · FRONTEND DEVELOPER @ PRIXA</text></g>')
    title = (f'<text x="40" y="640" font-family="{SANS}" font-weight="800" font-size="124" letter-spacing="-5" fill="{TXT}" textLength="1120" lengthAdjust="spacingAndGlyphs">Pratham Shrestha</text>')
    body = (
        f'<g transform="translate(600 340)"><g><animateTransform attributeName="transform" type="scale" values="1;1.06;1" dur="26s" repeatCount="indefinite"/>'
        f'<g transform="translate(-600 -340)"><image href="{img}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/></g></g></g>'
        f'<rect width="{W}" height="{H}" fill="url(#l)"/><rect width="{W}" height="{H}" fill="url(#b)"/>'
        f'<g>{tess}</g>'
        f'{strip(38)}'
        f'{reveal(tag, .35, -80, 0)}{reveal(roles, .45, 80, 8)}{reveal(status, 1.0, 0, 10, .7)}'
        f'{reveal(title, .7, 0, 60, 1.1)}'
        f'<line x1="48" x2="1152" y1="{H-18}" y2="{H-18}" stroke="{RED}" stroke-width="2" stroke-dasharray="1104" stroke-dashoffset="1104"><animate attributeName="stroke-dashoffset" from="1104" to="0" dur="1.4s" begin="1.2s" fill="freeze"/></line>')
    defs = (f'<linearGradient id="l" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BG}" stop-opacity=".88"/><stop offset=".5" stop-color="{BG}" stop-opacity=".2"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset=".55" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity=".92"/></linearGradient>')
    write("header.svg", doc(H, body, defs, "Pratham Shrestha - Full-Stack Developer from Nepal"))


# ---------------------------------------------------------------- SECTIONS
def section(idx, title):
    H = 150
    body = (strip(34) +
            reveal(f'<circle cx="62" cy="108" r="7" fill="{RED}"/><text x="86" y="124" font-family="{SANS}" font-weight="800" font-size="46" letter-spacing="1" fill="{TXT}">{title}</text>', .3, -30, 0, .8) +
            f'<text x="1152" y="122" text-anchor="end" font-family="{MONO}" font-size="14" fill="{DIM}">({idx})</text>')
    write(f"section-{idx}.svg", doc(H, body, label=title.title()))


# ------------------------------------------------------------------- ABOUT
def wrap(text, width_chars):
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > width_chars and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


def about():
    para = ("A passionate Full-Stack developer who loves building smooth, interactive, and visually clean web experiences. "
            "I turn ideas into responsive interfaces using modern tools, with a strong focus on animations, UX details, and performance. "
            "I'm especially into micro-interactions and scroll-based animations that make interfaces feel alive.")
    lines = wrap(para, 52)
    fs, lh = 27, 41
    words = para.split()
    total = len(words)
    DUR = 14
    out, wi = "", 0
    for li, line in enumerate(lines):
        spans = ""
        for w in line.split():
            t0 = .06 + .78 * wi / total
            kt = f"0;{t0:.3f};{min(t0+.04,.99):.3f};.92;1"
            spans += (f'<tspan opacity=".12">{esc(w)} <animate attributeName="opacity" dur="{DUR}s" repeatCount="indefinite" values=".12;.12;1;1;.12" keyTimes="{kt}"/></tspan>')
            wi += 1
        out += f'<text xml:space="preserve" x="400" y="{96+li*lh}" font-family="{SANS}" font-size="{fs}" letter-spacing="-.4" fill="{TXT}">{spans}</text>'
    H = 96 + len(lines) * lh + 40
    cy = H / 2 + 6
    pfp = (f'<defs><clipPath id="c"><circle cx="150" cy="{cy-30}" r="80"/></clipPath></defs>'
           f'<image href="{b64("pfp.jpg")}" x="70" y="{cy-110}" width="160" height="160" clip-path="url(#c)" preserveAspectRatio="xMidYMid slice"/>'
           f'<circle cx="150" cy="{cy-30}" r="80" fill="none" stroke="{RED}" stroke-width="5"/>'
           f'<text x="150" y="{cy+88}" text-anchor="middle" font-family="{MONO}" font-size="17" fill="{RED}">Pratham Shrestha</text>'
           f'<text x="150" y="{cy+112}" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{MUTED}">Full-Stack · MERN Developer</text>')
    write("about.svg", doc(H, pfp.replace("<defs>", "<g><defs>").replace("</defs>", "</defs>", 1) + "</g>" + out, label="About Pratham Shrestha"))


# -------------------------------------------------------------- EXPERIENCE
EXPERIENCE = [
    ("Frontend Developer", "Prixa (Ting Ting)", "Apr 2026 – Present", "Kupondole, Lalitpur", True,
     "Sole frontend dev on Inmark.ai: omnichannel inbox, real-time messaging, role-aware dashboards.",
     "React · Tailwind · shadcn/ui · Socket.io · TanStack Query"),
    ("Frontend Developer Intern", "Black Moon Pvt. Ltd.", "Feb 2026 – Apr 2026", "Ekantakuna, Lalitpur", False,
     "Agnikunda web app and a role-based Hospital Management System interface.",
     "React · MUI · MUI Charts"),
    ("Frontend Developer Intern", "TEDx Baneshwor", "Sep 2024 – Jan 2025", "Remote", False,
     "Built the official event landing page, matched to the event branding.",
     "Next.js"),
]


def experience():
    RH = 158
    H = 20 + RH * len(EXPERIENCE) + 20
    out = ""
    for i, (role, co, per, loc, cur, hl, stack) in enumerate(EXPERIENCE):
        y = 20 + i * RH
        chip = ""
        if cur:
            cx = 140 + len(role) * 20.5 + 18
            chip = (f'<rect x="{n(cx)}" y="{y+30}" width="92" height="28" rx="14" fill="{RED}"/><text x="{n(cx+46)}" y="{y+49}" text-anchor="middle" font-family="{MONO}" font-size="12" letter-spacing="1.5" fill="#fff">CURRENT</text>')
        row = (f'<line x1="48" x2="1152" y1="{y}" y2="{y}" stroke="{LINE}" stroke-width="1"/>'
               f'<text x="48" y="{y+54}" font-family="{MONO}" font-size="15" fill="{RED}">0{i+1}</text>'
               f'<text x="140" y="{y+58}" font-family="{SANS}" font-weight="700" font-size="36" letter-spacing="-1" fill="{TXT}">{esc(role)}</text>{chip}'
               f'<text x="140" y="{y+92}" font-family="{SANS}" font-size="20" fill="{MUTED}">{esc(co)} <tspan fill="{DIM}">— {esc(loc)}</tspan></text>'
               f'<text x="140" y="{y+126}" font-family="{SANS}" font-size="15" fill="{DIM}">{esc(hl)}</text>'
               f'<text x="1152" y="{y+54}" text-anchor="end" font-family="{MONO}" font-size="15" fill="{TXT}">{per}</text>'
               f'<text x="1152" y="{y+84}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{DIM}">{esc(stack)}</text>')
        out += reveal(row, .15 + i * .22, 0, 24, .8)
    out += f'<line x1="48" x2="1152" y1="{H-20}" y2="{H-20}" stroke="{LINE}" stroke-width="1"/>'
    write("experience.svg", doc(H, out, label="Experience: Prixa, Black Moon, TEDx Baneshwor"))


# ---------------------------------------------------------------- PROJECTS
PROJECTS = [
    ("Inmark AI", "Next.js · Tiptap · Motion · Claude", "inmark.ai", "p1.jpg"),
    ("Ochi Website Clone", "React · Tailwind · GSAP · Motion", "orchi.prathamshrestha69.com.np", "p2.jpg"),
    ("E-commerce Website", "React · Tailwind · GSAP", "e-commerce-omega-taupe-84.vercel.app", "p3.jpg"),
    ("Interview AI App", "React · Express · Node.js · MongoDB", "gdg-hackathon-frontend.vercel.app", "p4.jpg"),
    ("Susan Shrestha Portfolio", "React · Tailwind · GSAP", "susanshrestha404.com.np", "p5.jpg"),
]


def projects():
    RH = 168
    H = 20 + RH * len(PROJECTS) + 20
    out = ""
    for i, (name, stack, dom, img) in enumerate(PROJECTS):
        y = 20 + i * RH
        row = (f'<line x1="48" x2="1152" y1="{y}" y2="{y}" stroke="{LINE}" stroke-width="1"/>'
               f'<text x="48" y="{y+62}" font-family="{MONO}" font-size="15" fill="{RED}">0{i+1}</text>'
               f'<text x="140" y="{y+72}" font-family="{SANS}" font-weight="800" font-size="46" letter-spacing="-1.5" fill="{TXT}">{esc(name)}</text>'
               f'<text x="140" y="{y+108}" font-family="{MONO}" font-size="14" fill="{MUTED}">{esc(stack)}</text>'
               f'<text x="140" y="{y+136}" font-family="{MONO}" font-size="14" fill="{RED2}">↗ {esc(dom)}</text>'
               f'<defs><clipPath id="t{i}"><rect x="892" y="{y+22}" width="260" height="124" rx="10"/></clipPath></defs>'
               f'<image href="{b64(img)}" x="892" y="{y+22}" width="260" height="124" clip-path="url(#t{i})" preserveAspectRatio="xMidYMid slice"/>'
               f'<rect x="892" y="{y+22}" width="260" height="124" rx="10" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
        out += reveal(row, .15 + i * .18, 0, 24, .8)
    out += f'<line x1="48" x2="1152" y1="{H-20}" y2="{H-20}" stroke="{LINE}" stroke-width="1"/>'
    write("projects.svg", doc(H, out, label="Projects: Inmark AI, Ochi clone, E-commerce, Interview AI, Susan portfolio"))


# ------------------------------------------------------------------ SKILLS
def marquee_row(text_items, y, size, mode, direction, dur, sep_col=RED):
    unit = "".join(text_items)
    cw = size * .6
    unit_len = len(unit) + len(text_items) * 3  # " ● " separators
    tw = unit_len * cw

    def line(x):
        spans = ""
        for t in text_items:
            spans += f'<tspan>{esc(t)}</tspan><tspan fill="{sep_col}" stroke="none">  ●  </tspan>'
        if mode == "outline":
            st = f'fill="none" stroke="{TXT}" stroke-width="1.6"'
        else:
            st = f'fill="{TXT}"'
        return (f'<text xml:space="preserve" x="{n(x)}" y="{y}" font-family="{SANS}" font-weight="800" font-size="{size}" letter-spacing="-2" {st} '
                f'textLength="{n(tw)}" lengthAdjust="spacing">{spans}</text>')
    frm, to = ("0 0", f"-{n(tw)} 0") if direction < 0 else (f"-{n(tw)} 0", "0 0")
    return (f'<g><animateTransform attributeName="transform" type="translate" from="{frm}" to="{to}" dur="{dur}s" repeatCount="indefinite"/>'
            f'{line(0)}{line(tw)}</g>')


def skills():
    H = 470
    r1 = marquee_row(["REACT", "NEXT.JS", "TYPESCRIPT", "JAVASCRIPT", "NODE.JS"], 150, 120, "outline", -1, 38)
    r2 = marquee_row(["TAILWIND", "GSAP", "MOTION", "MONGODB", "MYSQL", "FIGMA"], 300, 120, "fill", 1, 44)
    r3 = marquee_row(["SOCKET.IO", "TANSTACK QUERY", "SHADCN/UI", "MUI", "REACT NATIVE", "TENSORFLOW", "GIT"], 395, 34, "fill", -1, 40, RED)
    body = (f'<line x1="0" x2="{W}" y1="20" y2="20" stroke="{LINE}"/><line x1="0" x2="{W}" y1="{H-20}" y2="{H-20}" stroke="{LINE}"/>'
            f'<g clip-path="url(#m)">{r1}{r2}{r3}</g>')
    defs = f'<clipPath id="m"><rect x="0" y="20" width="{W}" height="{H-40}"/></clipPath>'
    write("skills.svg", doc(H, body.replace('fill="#f4f4f5"', f'fill="{TXT}"'), defs, "Tech stack marquee: React, Next.js, TypeScript, JavaScript, Node.js, Tailwind, GSAP, Motion, MongoDB, MySQL, Figma"))


# ----------------------------------------------------------------- CONTACT
def contact():
    H = 520
    pent = wire(5, [(0, 3, 1, 0), (1, 4, 1, 0), (2, 3, 2, 0), (0, 2, 1, .5), (1, 2, 3, 0), (3, 4, 1, 0)], 930, 270, 120, 3.0, 120, 26,
                "#a1a1aa", [RED2, RED3], RED, BG, sw=1.5)
    para = "".join(f'<text x="48" y="{250+i*40}" font-family="{SANS}" font-weight="700" font-size="30" letter-spacing="-.8" fill="{TXT}">{t}</text>'
                   for i, t in enumerate(["HAVE AN IDEA IN MIND?", "LET'S CONNECT AND EXPLORE HOW", "I CAN HELP BRING IT TO LIFE."]))
    pfp = (f'<defs><clipPath id="c"><circle cx="86" cy="420" r="38"/></clipPath></defs>'
           f'<image href="{b64("pfp.jpg")}" x="48" y="382" width="76" height="76" clip-path="url(#c)" preserveAspectRatio="xMidYMid slice"/>'
           f'<circle cx="86" cy="420" r="38" fill="none" stroke="{RED}" stroke-width="4"/>'
           f'<text x="140" y="412" font-family="{MONO}" font-size="18" fill="{RED}">Pratham Shrestha</text>'
           f'<text x="140" y="436" font-family="{MONO}" font-size="13" fill="{MUTED}">Full-Stack Developer | MERN stack Developer</text>')
    body = (strip(34) + f'<g>{pent}</g>' +
            reveal(f'<text x="44" y="190" font-family="{SANS}" font-weight="800" font-size="120" letter-spacing="-5" fill="{TXT}" textLength="620" lengthAdjust="spacingAndGlyphs">LET\'S TALK</text>', .3, 0, 50, 1) +
            reveal(para, .6, 0, 30, .9) + reveal(pfp, .9, 0, 20, .8))
    write("contact.svg", doc(H, body, label="Let's talk"))


# ------------------------------------------------------------------ FOOTER
def footer():
    H = 230
    body = (strip(40) +
            reveal(f'<text x="48" y="170" font-family="{SANS}" font-weight="800" font-size="100" letter-spacing="-2" fill="{TXT}" textLength="1104" lengthAdjust="spacingAndGlyphs">PRATHAM SHRESTHA</text>', .3, 0, 90, 1.1) +
            f'<line x1="48" x2="1152" y1="196" y2="196" stroke="{RED}" stroke-width="2"/>'
            f'<text x="48" y="218" font-family="{MONO}" font-size="12" fill="{DIM}">© 2026 · KATHMANDU, NEPAL</text>')
    write("footer.svg", doc(H, body, label="Pratham Shrestha"))


if __name__ == "__main__":
    hero(); about(); experience(); projects(); skills(); contact(); footer()
    for i, t in enumerate(["ABOUT", "EXPERIENCE", "PROJECTS", "SKILLS", "ACTIVITY", "CONTACT"], 1):
        section(f"0{i}", t)
