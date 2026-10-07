#!/usr/bin/env python3
"""Generates the animated SVG assets used by README.md.

Everything is pure SVG/SMIL (GitHub strips JS/CSS from READMEs). The 3D/4D/5D
shapes are real n-dimensional rotations, projected to 2D and baked into
animation keyframes.   Run:  python3 .github/scripts/build_assets.py
"""
import itertools, math, os, random

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
os.makedirs(OUT, exist_ok=True)
random.seed(69)

CY, MG, LM, AM, VT = "#00f0ff", "#ff2bd6", "#b6ff3b", "#ffb020", "#8b5cff"
BG0, BG1 = "#05010f", "#14063d"
SANS = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"


def n(x):
    s = f"{x:.1f}"
    if s in ("-0.0", "0.0"):
        return "0"
    return s[:-2] if s.endswith(".0") else s


def write(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"{name:22s} {len(svg)/1024:7.1f} KB")


# ---------------------------------------------------------------- n-D math
def rot(v, i, j, a):
    v = list(v)
    c, s = math.cos(a), math.sin(a)
    v[i], v[j] = v[i] * c - v[j] * s, v[i] * s + v[j] * c
    return v


def project(v, cam=3.2, d=5.0):
    """n-D -> (x, y, scale). Successive perspective divides down to 3D, then 2D."""
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


def spin(p, t, planes):
    for (i, j, m, ph) in planes:
        p = rot(p, i, j, m * t + ph)
    return p


def anim(attr, vals, dur, extra=""):
    return (f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" '
            f'values="{";".join(vals)}" {extra}/>')


# ------------------------------------------------------- shared scene bits
def stars(W, H, count, tag):
    layers = []
    for li, (dur, rmax, op) in enumerate([(140, 0.9, .5), (90, 1.3, .75), (55, 1.9, 1)]):
        pts = []
        for _ in range(count // (li + 1) + 20):
            x, y = random.uniform(0, W), random.uniform(0, H * 0.8)
            r = random.uniform(.4, rmax)
            col = random.choice(["#fff", "#aef", "#fbe", "#cdf"])
            tw = ""
            if random.random() < .25:
                tw = anim("opacity", ["1", f"{random.uniform(.1,.4):.2f}", "1"], round(random.uniform(2, 5), 1))
            pts.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" fill="{col}" opacity="{op}">{tw}</circle>')
        layers.append(
            f'<g id="{tag}L{li}">{"".join(pts)}</g>'
        )
    body = ""
    for li, (dur, _, _) in enumerate([(140, 0, 0), (90, 0, 0), (55, 0, 0)]):
        body += (f'<g><animateTransform attributeName="transform" type="translate" '
                 f'from="0 0" to="-{W} 0" dur="{dur}s" repeatCount="indefinite"/>'
                 f'<use href="#{tag}L{li}"/><use href="#{tag}L{li}" x="{W}"/></g>')
    return "".join(layers).replace('<g id', '<g id'), body


def retro_floor(W, H, horizon, vpx, tag, gap=120, rows=9, dur=3):
    # moving horizontal lines + converging verticals, masked to fade at horizon
    fh = H - horizon

    def fy(u):
        return horizon + fh * (u ** 2.1)
    lines = []
    for j in range(rows):
        y0, y1 = fy(j / rows), fy((j + 1) / rows)
        op0, op1 = .1 + .9 * (j / rows), .1 + .9 * ((j + 1) / rows)
        lines.append(
            f'<line x1="0" x2="{W}" y1="{n(y0)}" y2="{n(y0)}" stroke="{MG}" stroke-width="1.6">'
            f'<animate attributeName="y1" dur="{dur}s" repeatCount="indefinite" values="{n(y0)};{n(y1)}"/>'
            f'<animate attributeName="y2" dur="{dur}s" repeatCount="indefinite" values="{n(y0)};{n(y1)}"/>'
            f'<animate attributeName="stroke-opacity" dur="{dur}s" repeatCount="indefinite" values="{op0:.2f};{op1:.2f}"/>'
            f'</line>')
    verts = []
    for i in range(-16, 17):
        verts.append(f'<line x1="{vpx}" y1="{horizon}" x2="{n(vpx + i * gap)}" y2="{H}" stroke="{CY}" stroke-width="1.2" stroke-opacity=".75"/>')
    return (
        f'<linearGradient id="{tag}fm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000"/><stop offset=".35" stop-color="#777"/><stop offset="1" stop-color="#fff"/></linearGradient>'
        f'<mask id="{tag}fmask"><rect x="0" y="{horizon}" width="{W}" height="{fh}" fill="url(#{tag}fm)"/></mask>',
        f'<g mask="url(#{tag}fmask)">{"".join(verts)}{"".join(lines)}</g>')


def sun(cx, cy, r, tag):
    stripes = "".join(
        f'<rect x="{cx-r-5}" y="{n(cy - r * .02 + i*i*2.6 + i*9)}" width="{2*r+10}" height="{n(1.5 + i*1.3)}" fill="#000"/>'
        for i in range(0, 9))
    defs = (f'<linearGradient id="{tag}sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe14a"/>'
            f'<stop offset=".5" stop-color="#ff7a3d"/><stop offset="1" stop-color="{MG}"/></linearGradient>'
            f'<radialGradient id="{tag}sh"><stop offset=".55" stop-color="{MG}" stop-opacity=".55"/><stop offset="1" stop-color="{MG}" stop-opacity="0"/></radialGradient>'
            f'<mask id="{tag}sm"><rect x="{cx-r-20}" y="{cy-r-20}" width="{2*r+40}" height="{2*r+40}" fill="#fff"/>{stripes}</mask>')
    body = (f'<circle cx="{cx}" cy="{cy}" r="{int(r*1.7)}" fill="url(#{tag}sh)">'
            f'<animate attributeName="r" values="{int(r*1.6)};{int(r*1.85)};{int(r*1.6)}" dur="5s" repeatCount="indefinite"/></circle>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{tag}sg)" mask="url(#{tag}sm)"/>')
    return defs, body


GLOW = ('<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<filter id="glow2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def extruded(text, x, y, size, textlen, depth=16, anchor="start", tag="t"):
    layers = []
    for i in range(depth, 0, -1):
        t = i / depth
        col = f"rgb({int(40+110*(1-t))},{int(8+10*(1-t))},{int(100+60*(1-t))})"
        layers.append(f'<text x="{n(x+i*.9)}" y="{n(y+i*.9)}" fill="{col}" text-anchor="{anchor}">{text}</text>')
    top = (f'<text x="{x}" y="{y}" fill="url(#{tag}tg)" text-anchor="{anchor}" filter="url(#glow2)">{text}</text>')
    grad = (f'<linearGradient id="{tag}tg" x1="0" y1="0" x2="1" y2="0" spreadMethod="reflect">'
            f'<stop offset="0" stop-color="{CY}"/><stop offset=".45" stop-color="#fff"/><stop offset=".7" stop-color="#ffd0f6"/><stop offset="1" stop-color="{MG}"/>'
            f'<animate attributeName="x1" values="0;1;0" dur="6s" repeatCount="indefinite"/>'
            f'<animate attributeName="x2" values="1;2;1" dur="6s" repeatCount="indefinite"/></linearGradient>')
    style = (f'font-family="{SANS}" font-weight="900" font-size="{size}" textLength="{textlen}" lengthAdjust="spacingAndGlyphs"')
    # textLength has to sit on each <text>
    g = "".join(layers) + top
    g = g.replace("<text ", f"<text {style} ")
    return grad, g


# ------------------------------------------------------------------ HEADER
def header():
    W, H, HOR = 1200, 460, 330
    N, DUR = 90, 18
    sdefs, sbody = stars(W, H, 90, "h")
    fdefs, fbody = retro_floor(W, H, HOR, 985, "h")
    udefs, ubody = sun(985, HOR, 125, "h")
    ph = (1 + 5 ** .5) / 2
    V = [(0, s1, s2 * ph) for s1 in (-1, 1) for s2 in (-1, 1)]
    V += [(s1, s2 * ph, 0) for s1 in (-1, 1) for s2 in (-1, 1)]
    V += [(s2 * ph, 0, s1) for s1 in (-1, 1) for s2 in (-1, 1)]
    nr = math.sqrt(1 + ph * ph)
    V = [tuple(c / nr for c in v) for v in V]
    E = [(a, b) for a in range(12) for b in range(a + 1, 12)
         if abs(sum((V[a][i] - V[b][i]) ** 2 for i in range(3)) - (2 / nr) ** 2) < 1e-6]
    F = []
    for a, b, c in itertools.combinations(range(12), 3):
        if (a, b) in E and (b, c) in E and (a, c) in E:
            F.append((a, b, c))
    assert len(E) == 30 and len(F) == 20, (len(E), len(F))
    CX, CYY, S = 985, 190, 98
    light = (-.45, -.6, -.65)
    ln = math.sqrt(sum(c * c for c in light))
    light = tuple(c / ln for c in light)

    def pose(p, t):
        p = rot(p, 0, 2, t)          # yaw
        p = rot(p, 1, 2, .45 + .22 * math.sin(2 * t))  # tilt wobble
        return p

    def scr(p):
        x, y, k = project(p, d=4.2)
        return CX + x * S * 1.0, CYY + y * S * 1.0, k

    face_pts = [[] for _ in F]; face_fill = [[] for _ in F]; face_op = [[] for _ in F]
    edge_vals = []
    hues = [(190 + 12 * i) % 360 for i in range(20)]
    import colorsys
    for k in range(N + 1):
        t = 2 * math.pi * k / N
        P = [pose(v, t) for v in V]
        Q = [scr(p) for p in P]
        for fi, (a, b, c) in enumerate(F):
            pa, pb, pc = P[a], P[b], P[c]
            u = [pb[i] - pa[i] for i in range(3)]; w = [pc[i] - pa[i] for i in range(3)]
            nm = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
            ctr = [(pa[i] + pb[i] + pc[i]) / 3 for i in range(3)]
            if sum(nm[i] * ctr[i] for i in range(3)) < 0:
                nm = [-c_ for c_ in nm]
            L = math.sqrt(sum(c_ * c_ for c_ in nm)); nm = [c_ / L for c_ in nm]
            br = max(0.0, sum(nm[i] * light[i] for i in range(3)))
            vis = max(0.0, min(1.0, -nm[2] * 6))
            hh = (hues[fi] + 40 * nm[0]) % 360
            r, g, bl = colorsys.hls_to_rgb(hh / 360, .2 + .45 * br, .85)
            face_fill[fi].append("#%02x%02x%02x" % (int(r * 255), int(g * 255), int(bl * 255)))
            face_op[fi].append(f"{vis*.78:.2f}")
            face_pts[fi].append(" ".join(f"{n(Q[i][0])},{n(Q[i][1])}" for i in (a, b, c)))
        edge_vals.append("".join(f"M{n(Q[a][0])} {n(Q[a][1])}L{n(Q[b][0])} {n(Q[b][1])}" for a, b in E))
    faces = "".join(
        f'<polygon fill="#888" stroke="#fff" stroke-opacity=".5" stroke-width=".8" stroke-linejoin="round">'
        f'{anim("points", face_pts[i], DUR)}{anim("fill", face_fill[i], DUR)}{anim("opacity", face_op[i], DUR)}</polygon>'
        for i in range(20))
    wire = (f'<path fill="none" stroke="#fff" stroke-opacity=".85" stroke-width="1.2" stroke-linecap="round">'
            f'{anim("d", edge_vals, DUR)}</path>')

    # gyroscope rings + orbiting satellites
    rings, sats = "", ""
    cfg = [(2, 0, 0, CY, 1.55), (3, 1, 1, MG, 1.75), (1, 2, 2, LM, 1.95)]
    for ri, (m, ax, ph0, col, rad) in enumerate(cfg):
        vals, sx, sy, sr = [], [], [], []
        for k in range(N + 1):
            t = 2 * math.pi * k / N
            pts = []
            for q in range(48):
                a = 2 * math.pi * q / 48
                p = [rad * math.cos(a), rad * math.sin(a), 0]
                p = rot(p, 0, 1, ph0)
                p = rot(p, 1, 2, 1.1 * ri + m * t * (1 if ri != 1 else -1))
                p = rot(p, 0, 2, 0.6 + (ri + 1) * t)
                pts.append(p)
            proj = [scr(p) for p in pts]
            vals.append("M" + "L".join(f"{n(x)} {n(y)}" for x, y, _ in proj) + "Z")
            # satellite
            a = (ri + 1) * 2 * math.pi * k / N * 1 + ri * 2
            p = [rad * math.cos(a), rad * math.sin(a), 0]
            p = rot(p, 0, 1, ph0); p = rot(p, 1, 2, 1.1 * ri + m * t * (1 if ri != 1 else -1)); p = rot(p, 0, 2, 0.6 + (ri + 1) * t)
            x, y, kk = scr(p)
            sx.append(n(x)); sy.append(n(y)); sr.append(n(4.2 * kk * kk))
        rings += (f'<path fill="none" stroke="{col}" stroke-width="1.6" stroke-opacity=".85" filter="url(#glow)">'
                  f'{anim("d", vals, DUR)}</path>')
        sats += (f'<circle fill="#fff" filter="url(#glow2)">{anim("cx", sx, DUR)}{anim("cy", sy, DUR)}{anim("r", sr, DUR)}</circle>')

    # typed subtitle
    phrases = ["Crafting interfaces that feel alive", "React  /  Next.js  /  TypeScript",
               "Dreaming in 3D, 4D & 5D", "Pixels, motion & good UX"]
    cw = 16.2
    typed, defs_clip = "", ""
    for i, ph_ in enumerate(phrases):
        Wd = len(ph_) * cw
        s = i * .25
        kt = [0, s, s + .07, s + .21, s + .25, 1]
        vv = [0, 0, Wd, Wd, 0, 0]
        pairs = []
        for a, b in zip(kt, vv):
            if pairs and abs(pairs[-1][0] - a) < 1e-9:
                pairs[-1] = (a, b)
            else:
                pairs.append((a, b))
        if pairs[-1][0] < 1:
            pairs.append((1, 0))
        kts = ";".join(f"{a:.3f}" for a, _ in pairs)
        wv = ";".join(n(b) for _, b in pairs)
        xv = ";".join(n(60 + b) for _, b in pairs)
        defs_clip += (f'<clipPath id="ty{i}"><rect x="60" y="250" height="50"><animate attributeName="width" dur="14s" repeatCount="indefinite" '
                      f'values="{wv}" keyTimes="{kts}"/></rect></clipPath>')
        typed += (f'<g clip-path="url(#ty{i})"><text x="60" y="282" font-family="{MONO}" font-size="27" fill="#e9e4ff" textLength="{n(Wd)}" lengthAdjust="spacingAndGlyphs">{ph_.replace("&","&amp;")}</text></g>'
                  f'<rect y="256" width="12" height="28" fill="{LM}" opacity=".95"><animate attributeName="x" dur="14s" repeatCount="indefinite" values="{xv}" keyTimes="{kts}"/>'
                  f'<animate attributeName="opacity" dur="14s" repeatCount="indefinite" values="{";".join("0" if b == 0 else "1" for _, b in pairs)}" keyTimes="{kts}"/></rect>')

    tg, title = extruded("PRATHAM SHRESTHA", 60, 215, 70, 740, tag="h")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Pratham Shrestha - Frontend Developer from Nepal">
<defs>
<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset=".72" stop-color="{BG1}"/><stop offset="1" stop-color="#2a0a52"/></linearGradient>
<linearGradient id="hfloor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a0a52"/><stop offset="1" stop-color="{BG0}"/></linearGradient>
<radialGradient id="hcore"><stop offset="0" stop-color="{CY}" stop-opacity=".5"/><stop offset="1" stop-color="{CY}" stop-opacity="0"/></radialGradient>
<clipPath id="hround"><rect width="{W}" height="{H}" rx="22"/></clipPath>
{GLOW}{sdefs}{fdefs}{udefs}{tg}{defs_clip}
</defs>
<g clip-path="url(#hround)">
<rect width="{W}" height="{H}" fill="url(#hbg)"/>
{sbody}
{ubody}
<rect y="{HOR}" width="{W}" height="{H-HOR}" fill="url(#hfloor)"/>
<line x1="0" x2="{W}" y1="{HOR}" y2="{HOR}" stroke="{CY}" stroke-width="2" filter="url(#glow)"/>
{fbody}
<circle cx="{CX}" cy="{CYY}" r="190" fill="url(#hcore)"><animate attributeName="r" values="170;205;170" dur="4s" repeatCount="indefinite"/></circle>
<g>{rings}{faces}{wire}{sats}</g>
<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="5s" repeatCount="indefinite"/>
<text x="60" y="118" font-family="{MONO}" font-size="17" fill="{CY}" letter-spacing="3" filter="url(#glow)">&#47;&#47; FRONTEND DEVELOPER  &#9670;  NEPAL</text>
{title}
</g>
{typed}
<text x="60" y="352" font-family="{MONO}" font-size="14" fill="#9d8cd8" letter-spacing="2">SCROLL DOWN  &#9660;  THERE ARE MORE DIMENSIONS</text>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="21" fill="none" stroke="{CY}" stroke-opacity=".35" stroke-width="2"/>
</g>
</svg>'''
    write("header.svg", svg)


# -------------------------------------------------------------- DIMENSIONS
def dimensions():
    W, H = 1200, 470
    cards = [
        dict(dim=3, label="3D", name="CUBE", info="8 vertices  /  12 edges", cx=215,
             planes=[(0, 2, 1, 0), (1, 2, 2, .6), (0, 1, 1, 0)], N=96, dur=14, S=118, cam=3.2),
        dict(dim=4, label="4D", name="TESSERACT", info="16 vertices  /  32 edges", cx=600,
             planes=[(0, 3, 1, 0), (1, 3, 2, 0), (0, 2, 1, .4), (1, 2, 2, 0)], N=120, dur=20, S=112, cam=2.6),
        dict(dim=5, label="5D", name="PENTERACT", info="32 vertices  /  80 edges", cx=985,
             planes=[(0, 3, 1, 0), (1, 4, 1, 0), (2, 3, 2, 0), (0, 2, 1, .5), (1, 2, 3, 0), (3, 4, 1, 0)], N=120, dur=24, S=104, cam=3.0),
    ]
    axis_col = [CY, MG, LM, AM, VT]
    body = ""
    for c in cards:
        verts, edges = hypercube(c["dim"])
        N, DUR, S, CXc, CYc = c["N"], c["dur"], c["S"], c["cx"], 255
        per_axis = {a: [] for a in range(c["dim"])}
        vx = [[] for _ in verts]; vy = [[] for _ in verts]; vr = [[] for _ in verts]
        for k in range(N + 1):
            t = 2 * math.pi * k / N
            Q = []
            for v in verts:
                p = spin([q / math.sqrt(c["dim"]) for q in v], t, c["planes"])
                x, y, kk = project(p, cam=c["cam"], d=4.0)
                Q.append((CXc + x * S, CYc + y * S, kk))
            for ax in range(c["dim"]):
                per_axis[ax].append("".join(f"M{n(Q[a][0])} {n(Q[a][1])}L{n(Q[b][0])} {n(Q[b][1])}" for a, b, d in edges if d == ax))
            for i, q in enumerate(Q):
                vx[i].append(n(q[0])); vy[i].append(n(q[1])); vr[i].append(n(max(1.4, 3.6 * q[2] ** 2)))
        paths = "".join(
            f'<path fill="none" stroke="{axis_col[ax]}" stroke-width="2" stroke-linecap="round" stroke-opacity=".92">{anim("d", per_axis[ax], DUR)}</path>'
            for ax in range(c["dim"]))
        dots = "".join(
            f'<circle fill="#fff" fill-opacity=".95">{anim("cx", vx[i], DUR)}{anim("cy", vy[i], DUR)}{anim("r", vr[i], DUR)}</circle>'
            for i in range(len(verts)))
        x0 = CXc - 170
        legend = "".join(
            f'<g transform="translate({x0+24+i*52} 418)"><rect width="14" height="4" y="-2" rx="2" fill="{axis_col[i]}"/>'
            f'<text x="20" y="4" font-family="{MONO}" font-size="12" fill="#b9acf0">{"xyzwv"[i]}</text></g>'
            for i in range(c["dim"]))
        body += f'''
<g>
<clipPath id="cc{c["dim"]}"><rect x="{x0}" y="100" width="340" height="300" rx="14"/></clipPath>
<rect x="{x0}" y="30" width="340" height="410" rx="20" fill="#0c0626" fill-opacity=".72" stroke="url(#dedge)" stroke-width="1.6"/>
<text x="{x0+24}" y="82" font-family="{SANS}" font-weight="900" font-size="46" fill="url(#dlab)" filter="url(#glow)">{c["label"]}</text>
<text x="{x0+100}" y="64" font-family="{MONO}" font-size="17" letter-spacing="3" fill="#fff">{c["name"]}</text>
<text x="{x0+100}" y="84" font-family="{MONO}" font-size="12" fill="#9d8cd8" letter-spacing="1">{c["info"]}</text>
<g clip-path="url(#cc{c["dim"]})"><g filter="url(#glow)">{paths}</g>{dots}</g>
{legend}
<text x="{x0+322}" y="84" text-anchor="end" font-family="{MONO}" font-size="11" fill="#6f5fb0"></text>
</g>'''
    sd, sb = stars(W, H, 70, "d")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Animated 3D cube, 4D tesseract and 5D penteract rotating">
<defs>
<linearGradient id="dbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
<linearGradient id="dedge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CY}" stop-opacity=".8"/><stop offset=".5" stop-color="{VT}" stop-opacity=".25"/><stop offset="1" stop-color="{MG}" stop-opacity=".8"/></linearGradient>
<linearGradient id="dlab" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CY}"/><stop offset="1" stop-color="{MG}"/></linearGradient>
<clipPath id="dround"><rect width="{W}" height="{H}" rx="22"/></clipPath>
{GLOW}{sd}
</defs>
<g clip-path="url(#dround)">
<rect width="{W}" height="{H}" fill="url(#dbg)"/>{sb}
{body}
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="21" fill="none" stroke="{VT}" stroke-opacity=".4" stroke-width="2"/>
</g>
</svg>'''
    write("dimensions.svg", svg)


# ------------------------------------------------------------ SKILL SPHERE
def skills():
    W, H = 1200, 560
    N, DUR = 120, 28
    CX, CYY, R = 600, 285, 205
    tags = ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "React Native", "Node.js",
            "Express", "MongoDB", "MySQL", "Figma", "TensorFlow", "Git", "UI/UX"]
    cols = [CY, MG, LM, AM, VT, "#ff7a3d", "#5cf0b8"]
    ga = math.pi * (3 - 5 ** .5)
    base = []
    for i in range(len(tags)):
        y = 1 - 2 * (i + .5) / len(tags)
        r = math.sqrt(1 - y * y)
        base.append((math.cos(i * ga) * r, y, math.sin(i * ga) * r))

    def pose(p, t):
        p = rot(p, 0, 2, t)
        return rot(p, 1, 2, .42 + .16 * math.sin(t))

    def scr(p, Rr=R):
        k = 800 / (800 + p[2] * Rr)
        return CX + p[0] * Rr * k, CYY + p[1] * Rr * k, k

    texts = ""
    data = [{"x": [], "y": [], "s": [], "o": []} for _ in tags]
    for k in range(N + 1):
        t = 2 * math.pi * k / N
        for i, b in enumerate(base):
            p = pose(b, t)
            x, y, _ = scr(p)
            front = (1 - p[2]) / 2
            data[i]["x"].append(n(x)); data[i]["y"].append(n(y))
            data[i]["s"].append(n(13 + 17 * front ** 1.3)); data[i]["o"].append(f"{.22 + .78 * front:.2f}")
    for i, tg in enumerate(tags):
        d = data[i]
        texts += (f'<text text-anchor="middle" dominant-baseline="middle" font-family="{SANS}" font-weight="800" fill="{cols[i % len(cols)]}" '
                  f'stroke="{BG0}" stroke-width="3.5" stroke-opacity=".75" paint-order="stroke" filter="url(#glow)">{tg}'
                  f'{anim("x", d["x"], DUR)}{anim("y", d["y"], DUR)}{anim("font-size", d["s"], DUR)}{anim("opacity", d["o"], DUR)}</text>')
    rings = ""
    for ri, (col, tilt, sp) in enumerate([(CY, 0.0, 1), (MG, 1.05, -1), (LM, 2.1, 2), (VT, .5, -2)]):
        vals = []
        for k in range(N + 1):
            t = 2 * math.pi * k / N
            pts = []
            for q in range(64):
                a = 2 * math.pi * q / 64
                p = [math.cos(a) * 1.0, math.sin(a) * 1.0, 0]
                p = rot(p, 1, 2, tilt + sp * t * .5 if ri else tilt)
                p = rot(rot(p, 0, 2, tilt * 1.7), 0, 2, t * (1 if ri % 2 == 0 else -1))
                p = rot(p, 1, 2, .42 + .16 * math.sin(t))
                pts.append(scr(p, R * 1.0)[:2])
            vals.append("M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts) + "Z")
        rings += f'<path fill="none" stroke="{col}" stroke-width="1" stroke-opacity=".38">{anim("d", vals, DUR)}</path>'
    sd, sb = stars(W, H, 80, "s")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Rotating 3D tag cloud of technologies: HTML, CSS, JavaScript, TypeScript, React, Next.js, React Native, Node, Express, MongoDB, MySQL, Figma, TensorFlow, Git, UI/UX">
<defs>
<radialGradient id="sbg" cx=".5" cy=".5" r=".75"><stop offset="0" stop-color="#1d0a52"/><stop offset="1" stop-color="{BG0}"/></radialGradient>
<radialGradient id="score"><stop offset="0" stop-color="{VT}" stop-opacity=".55"/><stop offset=".6" stop-color="{MG}" stop-opacity=".12"/><stop offset="1" stop-color="{MG}" stop-opacity="0"/></radialGradient>
<clipPath id="sround"><rect width="{W}" height="{H}" rx="22"/></clipPath>
{GLOW}{sd}
</defs>
<g clip-path="url(#sround)">
<rect width="{W}" height="{H}" fill="url(#sbg)"/>{sb}
<circle cx="{CX}" cy="{CYY}" r="{R+60}" fill="url(#score)"><animate attributeName="r" values="{R+40};{R+85};{R+40}" dur="6s" repeatCount="indefinite"/></circle>
{rings}
{texts}
<text x="44" y="52" font-family="{MONO}" font-size="15" letter-spacing="3" fill="{CY}">&#47;&#47; 3D TAG CLOUD</text>
<text x="{W-44}" y="{H-34}" text-anchor="end" font-family="{MONO}" font-size="13" letter-spacing="2" fill="#6f5fb0">PURE SVG  &#183;  NO JS  &#183;  ALWAYS SPINNING</text>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="21" fill="none" stroke="{MG}" stroke-opacity=".4" stroke-width="2"/>
</g>
</svg>'''
    write("skills.svg", svg)


# ------------------------------------------------------------ TERMINAL CARD
def about():
    W, H = 1200, 400
    DUR = 22
    lines = [
        (0.04, [("pratham@nepal", LM), (":~$ ", "#fff"), ("whoami", CY)]),
        (0.10, [("  Pratham Shrestha  ", "#fff"), ("// frontend developer", "#9d8cd8")]),
        (0.18, [("pratham@nepal", LM), (":~$ ", "#fff"), ("cat stack.txt", CY)]),
        (0.24, [("  React · Next.js · TypeScript · Node · MongoDB · Figma", "#ffd0f6")]),
        (0.33, [("pratham@nepal", LM), (":~$ ", "#fff"), ("./status --now", CY)]),
        (0.39, [("  ▸ exploring ", AM), ("Next.js, motion design & creative UI", "#fff")]),
        (0.45, [("  ▸ obsessed with ", AM), ("smooth animation, clean code, 3D on the web", "#fff")]),
        (0.53, [("pratham@nepal", LM), (":~$ ", "#fff")]),
    ]
    out = ""
    for idx, (ts, segs) in enumerate(lines):
        y = 112 + idx * 33
        spans = "".join(f'<tspan fill="{c}">{s.replace("&","&amp;")}</tspan>' for s, c in segs)
        kt = f"0;{ts:.3f};{ts+.015:.3f};1"
        out += (f'<text xml:space="preserve" x="44" y="{y}" font-family="{MONO}" font-size="21" opacity="0">{spans}'
                f'<animate attributeName="opacity" dur="{DUR}s" repeatCount="indefinite" values="0;0;1;1" keyTimes="{kt}"/></text>')
    cy = 112 + 7 * 33
    cursor = (f'<g opacity="0"><animate attributeName="opacity" dur="{DUR}s" repeatCount="indefinite" values="0;0;1;1" keyTimes="0;0.53;0.545;1"/>'
              f'<rect x="{44+len("pratham@nepal:~$ ")*12.6:.0f}" y="{cy-19}" width="12" height="25" fill="{LM}">'
              f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/></rect></g>')
    scan = "".join(f'<rect y="{y}" width="{W}" height="1" fill="#fff" opacity=".035"/>' for y in range(0, H, 4))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Terminal: whoami, Pratham Shrestha, frontend developer from Nepal">
<defs>
<linearGradient id="abg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b0620"/><stop offset="1" stop-color="#1a0942"/></linearGradient>
<linearGradient id="aedge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CY}"/><stop offset=".5" stop-color="{VT}"/><stop offset="1" stop-color="{MG}"/></linearGradient>
<linearGradient id="asweep" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CY}" stop-opacity="0"/><stop offset=".5" stop-color="{CY}" stop-opacity=".12"/><stop offset="1" stop-color="{CY}" stop-opacity="0"/></linearGradient>
<clipPath id="around"><rect width="{W}" height="{H}" rx="22"/></clipPath>
</defs>
<g clip-path="url(#around)">
<rect width="{W}" height="{H}" fill="url(#abg)"/>
<rect width="{W}" height="54" fill="#ffffff" fill-opacity=".05"/>
<circle cx="34" cy="27" r="7" fill="#ff5f56"/><circle cx="58" cy="27" r="7" fill="#ffbd2e"/><circle cx="82" cy="27" r="7" fill="#27c93f"/>
<text x="{W/2}" y="32" text-anchor="middle" font-family="{MONO}" font-size="14" fill="#9d8cd8" letter-spacing="2">pratham@nepal: ~/about</text>
{out}{cursor}
{scan}
<rect y="-120" width="{W}" height="120" fill="url(#asweep)"><animate attributeName="y" values="-120;{H}" dur="5s" repeatCount="indefinite"/></rect>
<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="21" fill="none" stroke="url(#aedge)" stroke-width="2.5"/>
</g>
</svg>'''
    write("about.svg", svg)


# ------------------------------------------------------- SECTION TITLES
def section(idx, text, sub):
    W, H = 1200, 110
    base = f'font-family="{SANS}" font-weight="900" font-size="46" text-anchor="middle" letter-spacing="4"'
    jit = lambda v: f'<animate attributeName="x" dur="4.5s" repeatCount="indefinite" calcMode="discrete" values="{v}" keyTimes="0;.62;.64;.66;.68;.70;.72;1"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{text}">
<defs>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CY}"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{MG}"/></linearGradient>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BG0}"/><stop offset=".5" stop-color="{BG1}"/><stop offset="1" stop-color="{BG0}"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CY}" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{MG}" stop-opacity="0"/></linearGradient>
<clipPath id="r"><rect width="{W}" height="{H}" rx="18"/></clipPath>
{GLOW}
</defs>
<g clip-path="url(#r)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<text x="{W/2+4}" y="64" fill="{MG}" opacity=".85" {base}>{text}{jit(f"{W/2+4};{W/2+4};{W/2+14};{W/2-10};{W/2+9};{W/2-4};{W/2+4};{W/2+4}")}</text>
<text x="{W/2-4}" y="60" fill="{CY}" opacity=".85" {base}>{text}{jit(f"{W/2-4};{W/2-4};{W/2-14};{W/2+10};{W/2-9};{W/2+4};{W/2-4};{W/2-4}")}</text>
<text x="{W/2}" y="62" fill="url(#g)" {base} filter="url(#glow)">{text}</text>
<text x="{W/2}" y="92" text-anchor="middle" font-family="{MONO}" font-size="14" letter-spacing="5" fill="#9d8cd8">{idx} &#47;&#47; {sub}</text>
<rect x="0" y="{H-4}" width="{W}" height="2" fill="url(#beam)" opacity=".8"/>
<rect y="{H-5}" width="160" height="4" rx="2" fill="#fff" filter="url(#glow)"><animate attributeName="x" values="-160;{W}" dur="3.2s" repeatCount="indefinite"/></rect>
</g>
</svg>'''
    write(f"section-{idx}.svg", svg)


# ------------------------------------------------------------------ FOOTER
def footer():
    W, H, HOR = 1200, 300, 175
    sd, sb = stars(W, H, 70, "f")
    fd, fb = retro_floor(W, H, HOR, 600, "f", gap=110, rows=8)
    ud, ub = sun(600, HOR, 105, "f")
    tg, title = extruded("THANKS FOR VISITING", 600, 112, 54, 760, depth=12, anchor="middle", tag="f")
    shoot = ""
    for i, (x, y, d, b) in enumerate([(200, 30, 1.6, 0), (900, 20, 2.1, 3), (500, 45, 1.9, 6)]):
        shoot += (f'<line x1="0" y1="0" x2="-70" y2="-22" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity="0">'
                  f'<animateTransform attributeName="transform" type="translate" values="{x} {y};{x+260} {y+82}" dur="{d+4}s" begin="{b}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;.08;.3" dur="{d+4}s" begin="{b}s" repeatCount="indefinite"/></line>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Thanks for visiting. Keep building, keep shipping.">
<defs>
<linearGradient id="fbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset=".6" stop-color="{BG1}"/><stop offset="1" stop-color="#2a0a52"/></linearGradient>
<linearGradient id="ffloor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a0a52"/><stop offset="1" stop-color="{BG0}"/></linearGradient>
<clipPath id="fround"><rect width="{W}" height="{H}" rx="22"/></clipPath>
{GLOW}{sd}{fd}{ud}{tg}
</defs>
<g clip-path="url(#fround)">
<rect width="{W}" height="{H}" fill="url(#fbg)"/>{sb}{shoot}{ub}
<rect y="{HOR}" width="{W}" height="{H-HOR}" fill="url(#ffloor)"/>
<line x1="0" x2="{W}" y1="{HOR}" y2="{HOR}" stroke="{CY}" stroke-width="2" filter="url(#glow)"/>
{fb}
<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0" dur="4s" repeatCount="indefinite"/>
{title}
<text x="600" y="152" text-anchor="middle" font-family="{MONO}" font-size="18" letter-spacing="6" fill="#ffd0f6" filter="url(#glow)">KEEP BUILDING  &#10022;  KEEP SHIPPING</text></g>
<text x="600" y="{H-16}" text-anchor="middle" font-family="{MONO}" font-size="12" letter-spacing="3" fill="#8b7bd0">MADE WITH PURE SVG  &#183;  NO JAVASCRIPT WAS HARMED</text>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="21" fill="none" stroke="{MG}" stroke-opacity=".4" stroke-width="2"/>
</g>
</svg>'''
    write("footer.svg", svg)


if __name__ == "__main__":
    header(); dimensions(); skills(); about()
    section("01", "WHO AM I", "ABOUT")
    section("02", "DIMENSIONS 3D · 4D · 5D", "REAL N-DIMENSIONAL ROTATION")
    section("03", "TECH STACK", "WHAT I BUILD WITH")
    section("04", "LIVE STATS", "THE NUMBERS")
    section("05", "CONTRIBUTIONS", "IN THREE DIMENSIONS")
    footer()
