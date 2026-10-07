#!/usr/bin/env python3
"""Generates the animated cartoon-style SVG assets used by README.md.

Pure SVG/SMIL (GitHub strips JS/CSS from READMEs). The 3D/4D/5D shapes are real
n-dimensional rotations, projected to 2D and baked into animation keyframes.
Run:  python3 .github/scripts/build_assets.py
"""
import itertools, math, os, random

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
os.makedirs(OUT, exist_ok=True)
random.seed(7)

INK, CREAM, DOT = "#1b1b2f", "#fff6e5", "#ecdcb8"
YEL, COR, MINT, SKY = "#ffd23f", "#ff6b6b", "#3ddc97", "#5bc0eb"
PUR, PNK, ORG, BLU, GRN = "#9b5de5", "#f15bb5", "#ff9f1c", "#3a86ff", "#2ecc71"
FONT = "'Arial Rounded MT Bold','Trebuchet MS',Verdana,'Segoe UI',Arial,sans-serif"
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


def anim(attr, vals, dur, extra=""):
    return (f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" '
            f'values="{";".join(vals)}" {extra}/>')


# ---------------------------------------------------------------- n-D math
def rot(v, i, j, a):
    v = list(v)
    c, s = math.cos(a), math.sin(a)
    v[i], v[j] = v[i] * c - v[j] * s, v[i] * s + v[j] * c
    return v


def project(v, cam=3.2, d=4.0):
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


# ------------------------------------------------------------ cartoon bits
DEFS = (f'<filter id="ol" x="-10%" y="-10%" width="120%" height="120%"><feMorphology in="SourceAlpha" operator="dilate" radius="2.6" result="d"/>'
        f'<feFlood flood-color="{INK}"/><feComposite in2="d" operator="in" result="o"/><feMerge><feMergeNode in="o"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="5" cy="5" r="2.2" fill="{DOT}"/></pattern>')


def sticker(x, y, w, h, fill, text, size=18, rot_=0, tc=INK, sh=5, extra=""):
    return (f'<g transform="rotate({rot_} {n(x+w/2)} {n(y+h/2)})" {extra}>'
            f'<rect x="{x+sh}" y="{y+sh}" width="{w}" height="{h}" rx="{h/2}" fill="{INK}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{fill}" stroke="{INK}" stroke-width="4"/>'
            f'<text x="{n(x+w/2)}" y="{n(y+h/2+size*.36)}" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="{size}" letter-spacing="1" fill="{tc}">{text}</text></g>')


def spark(x, y, s, dur, delay=0, fill=YEL):
    return (f'<g transform="translate({x} {y})"><g><animateTransform attributeName="transform" type="scale" values="0.3;1;0.3" dur="{dur}s" begin="{delay}s" repeatCount="indefinite"/>'
            f'<path transform="scale({s})" d="M0 -12 Q2 -2 12 0 Q2 2 0 12 Q-2 2 -12 0 Q-2 -2 0 -12Z" fill="{fill}" stroke="{INK}" stroke-width="{n(3/s)}" stroke-linejoin="round"/></g></g>')


def cloud(y, s, dur, delay, W=1200):
    shapes = [(0, 14, 30), (40, -6, 40), (86, 8, 32), (116, 16, 24)]
    ink = "".join(f'<circle cx="{x}" cy="{yy}" r="{r+4}" fill="{INK}"/>' for x, yy, r in shapes)
    ink += f'<rect x="-30" y="6" width="176" height="38" rx="19" fill="{INK}"/>'
    wh = "".join(f'<circle cx="{x}" cy="{yy}" r="{r}" fill="#fff"/>' for x, yy, r in shapes)
    wh += '<rect x="-26" y="10" width="168" height="30" rx="15" fill="#fff"/>'
    return (f'<g transform="translate(0 {y})"><g><animateTransform attributeName="transform" type="translate" from="-260 0" to="{W+100} 0" dur="{dur}s" begin="-{delay}s" repeatCount="indefinite"/>'
            f'<g transform="scale({s})">{ink}{wh}</g></g></g>')


def hills(W, H, y0):
    back = (f'<path d="M0 {y0+10} Q200 {y0-45} 430 {y0+5} T820 {y0-5} T{W} {y0-15} V{H} H0Z" fill="#8be28f" stroke="{INK}" stroke-width="5"/>')
    front = (f'<path d="M0 {y0+45} Q300 {y0-5} 640 {y0+40} T{W} {y0+25} V{H} H0Z" fill="{MINT}" stroke="{INK}" stroke-width="5"/>')
    return back + front


def tree(x, y, s, dur):
    return (f'<g transform="translate({x} {y}) scale({s})"><g><animateTransform attributeName="transform" type="rotate" values="-2.5 0 0;2.5 0 0;-2.5 0 0" dur="{dur}s" repeatCount="indefinite"/>'
            f'<rect x="-9" y="-40" width="18" height="44" rx="6" fill="#b5651d" stroke="{INK}" stroke-width="5"/>'
            f'<circle cx="0" cy="-70" r="42" fill="{GRN}" stroke="{INK}" stroke-width="5"/><circle cx="-14" cy="-80" r="10" fill="#fff" opacity=".35"/></g></g>')


def flower(x, y, col):
    return (f'<g transform="translate({x} {y})"><path d="M0 0 V-22" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
            f'<g transform="translate(0 -26)">{"".join(f"<circle cx=\"{n(9*math.cos(a))}\" cy=\"{n(9*math.sin(a))}\" r=\"6.5\" fill=\"{col}\" stroke=\"{INK}\" stroke-width=\"3\"/>" for a in [i*math.pi*2/5 for i in range(5)])}'
            f'<circle r="5.5" fill="{YEL}" stroke="{INK}" stroke-width="3"/></g></g>')


def sun(cx, cy, r, rays=12):
    rs = "".join(f'<path d="M{n(math.cos(a)*(r+10))} {n(math.sin(a)*(r+10))} L{n(math.cos(a+.13)*(r+30))} {n(math.sin(a+.13)*(r+30))} L{n(math.cos(a-.13)*(r+30))} {n(math.sin(a-.13)*(r+30))}Z" fill="{ORG}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
                 for a in [i * math.pi * 2 / rays for i in range(rays)])
    return (f'<g transform="translate({cx} {cy})"><g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="40s" repeatCount="indefinite"/>{rs}</g>'
            f'<circle r="{r}" fill="{YEL}" stroke="{INK}" stroke-width="5"/><path d="M{-r*.55} {-r*.3} Q{-r*.3} {-r*.65} {r*.1} {-r*.65}" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity=".8"/>'
            f'<circle cx="{-r*.3}" cy="{r*.1}" r="5" fill="{INK}"/><circle cx="{r*.3}" cy="{r*.1}" r="5" fill="{INK}"/>'
            f'<path d="M{-r*.3} {r*.38} Q0 {r*.65} {r*.3} {r*.38}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/></g>')


def mascot(cx, cy, s=1.0):
    arm = lambda x0, y0, x1, y1: (f'<path d="M{x0} {y0} L{x1} {y1}" stroke="{INK}" stroke-width="22" stroke-linecap="round"/>'
                                   f'<path d="M{x0} {y0} L{x1} {y1}" stroke="{PUR}" stroke-width="12" stroke-linecap="round"/>')
    return (f'<g transform="translate({cx} {cy}) scale({s})">'
            f'<ellipse cx="0" cy="132" rx="74" ry="11" fill="{INK}" opacity=".2"><animate attributeName="rx" values="74;62;74" dur="2.2s" repeatCount="indefinite"/></ellipse>'
            f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -9;0 0" dur="2.2s" repeatCount="indefinite" calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1"/>'
            f'<ellipse cx="-34" cy="118" rx="22" ry="12" fill="{ORG}" stroke="{INK}" stroke-width="5"/><ellipse cx="34" cy="118" rx="22" ry="12" fill="{ORG}" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M0 -95 V-132" stroke="{INK}" stroke-width="6" stroke-linecap="round"/><circle cx="0" cy="-142" r="13" fill="{YEL}" stroke="{INK}" stroke-width="5"><animate attributeName="r" values="13;16;13" dur="1.4s" repeatCount="indefinite"/></circle>'
            + arm(-84, 20, -112, 62) +
            f'<g><animateTransform attributeName="transform" type="rotate" values="0 84 20;-38 84 20;0 84 20;-38 84 20;0 84 20" keyTimes="0;.12;.24;.36;1" dur="4s" repeatCount="indefinite"/>'
            + arm(84, 20, 120, -30) +
            f'<circle cx="122" cy="-34" r="14" fill="{CREAM}" stroke="{INK}" stroke-width="5"/></g>'
            f'<rect x="-92" y="-82" width="184" height="200" rx="72" fill="{PUR}" stroke="{INK}" stroke-width="6"/>'
            f'<path d="M-70 -50 Q-72 -70 -50 -72" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" opacity=".45"/>'
            f'<rect x="-66" y="-54" width="132" height="104" rx="42" fill="{CREAM}" stroke="{INK}" stroke-width="4"/>'
            f'<ellipse cx="-26" cy="-16" rx="11" ry="14" fill="{INK}"><animate attributeName="ry" values="14;14;1.5;14;14" keyTimes="0;.9;.93;.96;1" dur="4s" repeatCount="indefinite"/></ellipse>'
            f'<ellipse cx="26" cy="-16" rx="11" ry="14" fill="{INK}"><animate attributeName="ry" values="14;14;1.5;14;14" keyTimes="0;.9;.93;.96;1" dur="4s" repeatCount="indefinite"/></ellipse>'
            f'<circle cx="-22" cy="-21" r="4" fill="#fff"/><circle cx="30" cy="-21" r="4" fill="#fff"/>'
            f'<circle cx="-46" cy="12" r="8" fill="{PNK}" opacity=".7"/><circle cx="46" cy="12" r="8" fill="{PNK}" opacity=".7"/>'
            f'<path d="M-19 8 Q0 36 19 8Z" fill="{INK}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/><path d="M-9 19 Q0 31 9 19Z" fill="{COR}"/>'
            f'<text x="0" y="96" text-anchor="middle" font-family="{MONO}" font-weight="900" font-size="26" fill="{YEL}" stroke="{INK}" stroke-width="5" paint-order="stroke">&lt;/&gt;</text>'
            f'</g></g>')


def banner_scene(W, H):
    return f'<rect width="{W}" height="{H}" fill="#8fd8ff"/><rect y="{int(H*.55)}" width="{W}" height="{H}" fill="#b9e8ff" opacity=".6"/>'


def typed_bubble(x, y, w, h, phrases, size=26, cw=14.4, dur=14):
    out = (f'<g><rect x="{x+6}" y="{y+6}" width="{w}" height="{h}" rx="{h/2}" fill="{INK}"/><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="#fff" stroke="{INK}" stroke-width="5"/>'
           f'<path d="M{x+46} {y+h-2} L{x+34} {y+h+26} L{x+82} {y+h-2}Z" fill="#fff" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/><path d="M{x+42} {y+h-1} H{x+84}" stroke="#fff" stroke-width="8"/></g>')
    defs = ""
    tx, ty = x + 34, y + h / 2
    for i, ph in enumerate(phrases):
        Wd = len(ph) * cw
        s = i / len(phrases)
        e = (i + 1) / len(phrases)
        kt = [0, s, s + .07, e - .04, e - .01, 1]
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
        xv = ";".join(n(tx + b) for _, b in pairs)
        ov = ";".join("0" if b == 0 else "1" for _, b in pairs)
        defs += (f'<clipPath id="ty{i}"><rect x="{tx}" y="{y}" height="{h}"><animate attributeName="width" dur="{dur}s" repeatCount="indefinite" values="{wv}" keyTimes="{kts}"/></rect></clipPath>')
        out += (f'<g clip-path="url(#ty{i})"><text x="{tx}" y="{n(ty+size*.35)}" font-family="{FONT}" font-weight="900" font-size="{size}" fill="{INK}" textLength="{n(Wd)}" lengthAdjust="spacingAndGlyphs">{ph.replace("&","&amp;")}</text></g>'
                f'<rect y="{n(ty-size*.6)}" width="5" height="{n(size*1.2)}" rx="2" fill="{COR}"><animate attributeName="x" dur="{dur}s" repeatCount="indefinite" values="{xv}" keyTimes="{kts}"/>'
                f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" values="{ov}" keyTimes="{kts}"/></rect>')
    return defs, out


# ------------------------------------------------------------------ HEADER
def header():
    W, H = 1200, 440
    N, DUR = 90, 14
    CX, CYY, S = 950, 225, 66
    base_cols = [COR, YEL, MINT, SKY, PUR, PNK]
    faces = []
    for a in range(3):
        for sgn in (-1, 1):
            b, c = [i for i in range(3) if i != a]
            quad = []
            for (u, v) in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                p = [0, 0, 0]; p[a] = sgn; p[b] = u; p[c] = v
                quad.append(p)
            nrm = [0, 0, 0]; nrm[a] = sgn
            faces.append((quad, nrm))
    light = (-.4, -.7, -.6)
    ln = math.sqrt(sum(x * x for x in light)); light = tuple(x / ln for x in light)

    def pose(p, t):
        p = rot(p, 0, 2, t)
        return rot(p, 1, 2, .5 + .25 * math.sin(2 * t))

    pts = [[] for _ in faces]; fills = [[] for _ in faces]; vis = [[] for _ in faces]
    for k in range(N + 1):
        t = 2 * math.pi * k / N
        for fi, (quad, nrm) in enumerate(faces):
            P = [pose([q / 1.0 for q in v], t) for v in quad]
            nm = pose(nrm, t)
            sc = []
            for p in P:
                x, y, kk = project(p, d=6.5)
                sc.append(f"{n(CX + x * S)},{n(CYY + y * S)}")
            pts[fi].append(" ".join(sc))
            br = max(0.0, sum(nm[i] * light[i] for i in range(3)) * -1)
            br = max(0.0, -sum(nm[i] * light[i] for i in range(3)))
            f = .86 + .14 * br
            col = base_cols[fi]
            r, g, b_ = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
            fills[fi].append("#%02x%02x%02x" % (int(r * f), int(g * f), int(b_ * f)))
            vis[fi].append("1" if nm[2] < 0 else "0")
    cube = "".join(
        f'<polygon fill="#888" stroke="{INK}" stroke-width="6" stroke-linejoin="round">{anim("points", pts[i], DUR)}{anim("fill", fills[i], DUR)}'
        f'<animate attributeName="opacity" dur="{DUR}s" repeatCount="indefinite" calcMode="discrete" values="{";".join(vis[i])}"/></polygon>'
        for i in range(6))

    bd, bubble = typed_bubble(60, 292, 600, 58, ["Crafting interfaces that feel alive", "React, Next.js & TypeScript",
                                                 "Turning ideas into pixels", "Dreaming in 3D, 4D & 5D"])
    title = lambda txt, y, tl: (f'<text x="66" y="{y+7}" font-family="{FONT}" font-weight="900" font-size="88" fill="{INK}" stroke="{INK}" stroke-width="14" stroke-linejoin="round" textLength="{tl}" lengthAdjust="spacingAndGlyphs">{txt}</text>'
                                 f'<text x="60" y="{y}" font-family="{FONT}" font-weight="900" font-size="88" fill="{YEL}" stroke="{INK}" stroke-width="12" stroke-linejoin="round" paint-order="stroke" textLength="{tl}" lengthAdjust="spacingAndGlyphs">{txt}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Pratham Shrestha - Frontend Developer from Nepal">
<defs>{DEFS}{bd}<clipPath id="rr"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>
<g clip-path="url(#rr)">
{banner_scene(W, H)}
{sun(1075, 88, 42)}
{cloud(60, 1.0, 70, 10)}{cloud(150, .7, 95, 55)}{cloud(24, .8, 120, 80)}
{hills(W, H, 372)}
{tree(150, 408, .8, 3.4)}{tree(700, 420, .6, 4.1)}{tree(1130, 415, .75, 3.7)}
{flower(260, 428, PNK)}{flower(520, 430, COR)}{flower(870, 428, "#fff")}{flower(1010, 430, ORG)}
<ellipse cx="{CX}" cy="400" rx="92" ry="14" fill="{INK}" opacity=".25"><animate attributeName="rx" values="92;70;92" dur="1.6s" repeatCount="indefinite"/></ellipse>
<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -22;0 0" dur="1.6s" repeatCount="indefinite" calcMode="spline" keySplines=".33 0 .67 1;.33 0 .67 1"/>{cube}</g>
{spark(860, 95, 1.3, 2.2)}{spark(1110, 250, 1.1, 2.8, .6)}{spark(865, 330, 1, 2.5, 1.1, PNK)}{spark(1140, 160, .9, 2.1, .3, "#fff")}
{sticker(60, 34, 262, 40, COR, "FRONTEND DEVELOPER", 18, -2, "#fff")}{sticker(342, 38, 150, 38, MINT, "FROM NEPAL", 18, 2)}
<text x="60" y="118" font-family="{FONT}" font-weight="900" font-size="28" fill="{INK}" letter-spacing="2">HELLO WORLD, I'M</text>
<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0" dur="3s" repeatCount="indefinite"/>
{title("PRATHAM", 200, 440)}{title("SHRESTHA", 282, 500)}</g>
{bubble}
<rect x="2.5" y="2.5" width="{W-5}" height="{H-5}" rx="26" fill="none" stroke="{INK}" stroke-width="5"/>
</g>
</svg>'''
    write("header.svg", svg)


# -------------------------------------------------------------- DIMENSIONS
def dimensions():
    W, H = 1200, 500
    cards = [
        dict(dim=3, label="3D", name="CUBE", info="8 vertices  ·  12 edges", x=30, col="#bfe9ff",
             planes=[(0, 2, 1, 0), (1, 2, 2, .6), (0, 1, 1, 0)], N=96, dur=14, S=118, cam=3.2),
        dict(dim=4, label="4D", name="TESSERACT", info="16 vertices  ·  32 edges", x=420, col="#ffe58f",
             planes=[(0, 3, 1, 0), (1, 3, 2, 0), (0, 2, 1, .4), (1, 2, 2, 0)], N=120, dur=20, S=112, cam=2.6),
        dict(dim=5, label="5D", name="PENTERACT", info="32 vertices  ·  80 edges", x=810, col="#ffc9e6",
             planes=[(0, 3, 1, 0), (1, 4, 1, 0), (2, 3, 2, 0), (0, 2, 1, .5), (1, 2, 3, 0), (3, 4, 1, 0)], N=120, dur=24, S=104, cam=3.0),
    ]
    axis_col = [COR, PUR, GRN, ORG, BLU]
    body = ""
    for c in cards:
        verts, edges = hypercube(c["dim"])
        N, DUR, S, x0 = c["N"], c["dur"], c["S"], c["x"]
        CXc, CYc = x0 + 180, 285
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
                vx[i].append(n(q[0])); vy[i].append(n(q[1])); vr[i].append(n(max(3, 6.5 * q[2] ** 2)))
        paths = "".join(
            f'<path fill="none" stroke="{axis_col[ax]}" stroke-width="5" stroke-linecap="round">{anim("d", per_axis[ax], DUR)}</path>'
            for ax in range(c["dim"]))
        dots = "".join(
            f'<circle fill="#fff" stroke="{INK}" stroke-width="3">{anim("cx", vx[i], DUR)}{anim("cy", vy[i], DUR)}{anim("r", vr[i], DUR)}</circle>'
            for i in range(len(verts)))
        legend = "".join(
            f'<g transform="translate({x0+34+i*56} 438)"><circle r="9" fill="{axis_col[i]}" stroke="{INK}" stroke-width="3.5"/>'
            f'<text x="17" y="6" font-family="{FONT}" font-weight="900" font-size="16" fill="{INK}">{"xyzwv"[i]}</text></g>'
            for i in range(c["dim"]))
        body += f'''
<g>
<clipPath id="cc{c["dim"]}"><rect x="{x0}" y="140" width="360" height="270"/></clipPath>
<rect x="{x0+9}" y="39" width="360" height="440" rx="26" fill="{INK}"/>
<rect x="{x0}" y="30" width="360" height="440" rx="26" fill="{c["col"]}" stroke="{INK}" stroke-width="5"/>
<rect x="{x0}" y="30" width="360" height="104" rx="26" fill="{c["col"]}"/><path d="M{x0} 134 H{x0+360}" stroke="{INK}" stroke-width="5"/>
<rect x="{x0+20}" y="48" width="104" height="70" rx="20" fill="#fff" stroke="{INK}" stroke-width="5"/>
<text x="{x0+72}" y="100" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="46" fill="{INK}">{c["label"]}</text>
<text x="{x0+142}" y="82" font-family="{FONT}" font-weight="900" font-size="24" fill="{INK}">{c["name"]}</text>
<text x="{x0+142}" y="106" font-family="{FONT}" font-weight="700" font-size="14" fill="{INK}" opacity=".75">{c["info"]}</text>
<g clip-path="url(#cc{c["dim"]})"><g filter="url(#ol)">{paths}</g>{dots}</g>
{legend}
</g>'''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Animated 3D cube, 4D tesseract and 5D penteract rotating">
<defs>{DEFS}<clipPath id="rr"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>
<g clip-path="url(#rr)"><rect width="{W}" height="{H}" fill="{CREAM}"/><rect width="{W}" height="{H}" fill="url(#dots)"/>
{body}
<rect x="2.5" y="2.5" width="{W-5}" height="{H-5}" rx="26" fill="none" stroke="{INK}" stroke-width="5"/></g>
</svg>'''
    write("dimensions.svg", svg)


# ------------------------------------------------------------ SKILL PLANET
def skills():
    W, H = 1200, 560
    N, DUR = 120, 30
    CX, CYY, R = 600, 290, 235
    tags = ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "React Native", "Node.js",
            "Express", "MongoDB", "MySQL", "Figma", "TensorFlow", "Git", "UI/UX"]
    cols = [YEL, "#ffb3d9", "#8ff0c5", "#9ad9ff", "#ffc27a", "#d3b8ff", "#ffa8a8"]
    ga = math.pi * (3 - 5 ** .5)
    base = []
    for i in range(len(tags)):
        y = 1 - 2 * (i + .5) / len(tags)
        r = math.sqrt(1 - y * y)
        base.append((math.cos(i * ga) * r, y, math.sin(i * ga) * r))

    def pose(p, t):
        p = rot(p, 0, 2, t)
        return rot(p, 1, 2, .42 + .16 * math.sin(t))

    data = [{"t": [], "s": [], "o": []} for _ in tags]
    for k in range(N + 1):
        t = 2 * math.pi * k / N
        for i, b in enumerate(base):
            p = pose(b, t)
            kk = 800 / (800 + p[2] * R)
            front = (1 - p[2]) / 2
            data[i]["t"].append(f"{n(CX + p[0]*R*kk)} {n(CYY + p[1]*R*kk*.82)}")
            data[i]["s"].append(f"{.6 + .62 * front:.2f}")
            data[i]["o"].append(f"{.5 + .5 * front:.2f}")
    pills = ""
    for i, tg in enumerate(tags):
        d = data[i]
        w = len(tg) * 10.4 + 34
        pills += (f'<g opacity="1">{anim("opacity", d["o"], DUR)}<g>'
                  f'<animateTransform attributeName="transform" type="translate" dur="{DUR}s" repeatCount="indefinite" values="{";".join(d["t"])}"/>'
                  f'<animateTransform attributeName="transform" type="scale" additive="sum" dur="{DUR}s" repeatCount="indefinite" values="{";".join(d["s"])}"/>'
                  f'<rect x="{n(-w/2+4)}" y="-14" width="{n(w)}" height="38" rx="19" fill="{INK}"/>'
                  f'<rect x="{n(-w/2)}" y="-20" width="{n(w)}" height="38" rx="19" fill="{cols[i % len(cols)]}" stroke="{INK}" stroke-width="4"/>'
                  f'<text x="0" y="5" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="17" fill="{INK}" textLength="{n(len(tg)*10.4)}" lengthAdjust="spacingAndGlyphs">{tg}</text>'
                  f'</g></g>')
    planet = (f'<g transform="translate({CX} {CYY})"><g><animateTransform attributeName="transform" type="translate" values="0 0;0 -8;0 0" dur="3s" repeatCount="indefinite"/>'
              f'<circle r="86" fill="{PUR}" stroke="{INK}" stroke-width="6"/>'
              f'<path d="M-60 -40 Q-40 -66 -4 -70" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" opacity=".5"/>'
              f'<circle cx="34" cy="26" r="14" fill="#7c3fc7"/><circle cx="-26" cy="38" r="9" fill="#7c3fc7"/>'
              f'<ellipse rx="140" ry="34" transform="rotate(-18)" fill="none" stroke="{INK}" stroke-width="20"/><ellipse rx="140" ry="34" transform="rotate(-18)" fill="none" stroke="{YEL}" stroke-width="11"/>'
              f'<text y="14" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="38" fill="#fff" stroke="{INK}" stroke-width="7" paint-order="stroke">STACK</text></g></g>')
    orbit = f'<ellipse cx="{CX}" cy="{CYY}" rx="{R}" ry="{int(R*.82)}" fill="none" stroke="{INK}" stroke-width="3" stroke-dasharray="3 14" stroke-linecap="round" opacity=".45"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Rotating 3D tag cloud of technologies: HTML, CSS, JavaScript, TypeScript, React, Next.js, React Native, Node, Express, MongoDB, MySQL, Figma, TensorFlow, Git, UI/UX">
<defs>{DEFS}<clipPath id="rr"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>
<g clip-path="url(#rr)"><rect width="{W}" height="{H}" fill="#e6dcff"/><rect width="{W}" height="{H}" fill="url(#dots)" opacity=".7"/>
{orbit}{planet}{pills}
{spark(110, 90, 1.4, 2.4)}{spark(1090, 120, 1.1, 2.9, .5, PNK)}{spark(150, 470, 1, 2.6, 1)}{spark(1060, 470, 1.3, 2.2, .2, "#fff")}
{sticker(44, 36, 232, 40, YEL, "SPINNING TECH CLOUD", 15, -3)}
<rect x="2.5" y="2.5" width="{W-5}" height="{H-5}" rx="26" fill="none" stroke="{INK}" stroke-width="5"/></g>
</svg>'''
    write("skills.svg", svg)


# ------------------------------------------------------------------- ABOUT
def about():
    W, H = 1200, 420
    rows = [("NAME", COR, "Pratham Shrestha"), ("ROLE", YEL, "Frontend Developer"), ("FROM", MINT, "Nepal"),
            ("STACK", SKY, "React · Next.js · TypeScript · Node"), ("NOW", PNK, "Exploring Next.js, motion & creative UI")]
    rr = ""
    for i, (lab, col, val) in enumerate(rows):
        y = 106 + i * 50
        rr += (f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur=".01s" begin="{.25+i*.25}s" fill="freeze"/>'
               f'<animateTransform attributeName="transform" type="translate" from="40 0" to="0 0" dur=".35s" begin="{.25+i*.25}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 1.4 .4 1"/>'
               f'<rect x="{442+5}" y="{y+5}" width="118" height="38" rx="19" fill="{INK}"/><rect x="442" y="{y}" width="118" height="38" rx="19" fill="{col}" stroke="{INK}" stroke-width="4"/>'
               f'<text x="501" y="{y+25}" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="16" letter-spacing="1" fill="{INK}">{lab}</text>'
               f'<text x="584" y="{y+27}" font-family="{FONT}" font-weight="900" font-size="23" fill="{INK}">{val.replace("&","&amp;")}</text></g>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="About: Pratham Shrestha, frontend developer from Nepal">
<defs>{DEFS}<clipPath id="rr"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>
<g clip-path="url(#rr)"><rect width="{W}" height="{H}" fill="{CREAM}"/><rect width="{W}" height="{H}" fill="url(#dots)"/>
<rect x="49" y="49" width="340" height="340" rx="30" fill="{INK}"/><rect x="40" y="40" width="340" height="340" rx="30" fill="#8fd8ff" stroke="{INK}" stroke-width="5"/>
<path d="M45 330 Q200 300 375 335 V350 Q375 375 350 375 H70 Q45 375 45 350Z" fill="{MINT}" stroke="{INK}" stroke-width="5"/>
{mascot(210, 210, .95)}
<rect x="429" y="49" width="738" height="320" rx="30" fill="{INK}"/><rect x="420" y="40" width="738" height="320" rx="30" fill="#fff" stroke="{INK}" stroke-width="5"/>
{rr}
{sticker(450, 56, 190, 38, ORG, "ABOUT ME!", 18, -2)}
<rect x="2.5" y="2.5" width="{W-5}" height="{H-5}" rx="26" fill="none" stroke="{INK}" stroke-width="5"/></g>
</svg>'''
    write("about.svg", svg)


# --------------------------------------------------------- SECTION BANNERS
def section(idx, text, col):
    W, H = 1200, 120
    w = len(text) * 29 + 150
    x = (W - w) / 2
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{text}">
<g><animateTransform attributeName="transform" type="rotate" values="-1.2 600 60;1.2 600 60;-1.2 600 60" dur="4s" repeatCount="indefinite" calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1"/>
<rect x="{n(x+8)}" y="{28+8}" width="{w}" height="64" rx="32" fill="{INK}"/>
<rect x="{n(x)}" y="28" width="{w}" height="64" rx="32" fill="{col}" stroke="{INK}" stroke-width="5"/>
<circle cx="{n(x+38)}" cy="60" r="24" fill="#fff" stroke="{INK}" stroke-width="5"/>
<text x="{n(x+38)}" y="67" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="20" fill="{INK}">{idx}</text>
<text x="{n(x+w/2+30)}" y="74" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="38" letter-spacing="2" fill="#fff" stroke="{INK}" stroke-width="8" stroke-linejoin="round" paint-order="stroke">{text}</text>
</g></svg>'''
    write(f"section-{idx}.svg", svg)


# ------------------------------------------------------------------ FOOTER
def footer():
    W, H = 1200, 320
    word = "THANKS FOR VISITING!"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Thanks for visiting! Keep building, keep shipping.">
<defs>{DEFS}<clipPath id="rr"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>
<g clip-path="url(#rr)">
{banner_scene(W, H)}
{sun(1090, 80, 38)}
{cloud(40, .9, 80, 20)}{cloud(120, .6, 100, 70)}
{hills(W, H, 250)}
{tree(1000, 300, .7, 3.6)}{tree(120, 305, .6, 4)}
{flower(330, 300, PNK)}{flower(860, 304, COR)}{flower(930, 300, "#fff")}
{mascot(120, 160, .5)}
<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="2.6s" repeatCount="indefinite"/>
<text x="646" y="132" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="54" fill="{INK}" stroke="{INK}" stroke-width="14" stroke-linejoin="round" textLength="680" lengthAdjust="spacingAndGlyphs">{word}</text>
<text x="640" y="126" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="54" fill="{YEL}" stroke="{INK}" stroke-width="12" stroke-linejoin="round" paint-order="stroke" textLength="680" lengthAdjust="spacingAndGlyphs">{word}</text></g>
{sticker(470, 160, 340, 42, PNK, "KEEP BUILDING · KEEP SHIPPING", 17, -1.5, "#fff")}
<rect x="2.5" y="2.5" width="{W-5}" height="{H-5}" rx="26" fill="none" stroke="{INK}" stroke-width="5"/>
</g></svg>'''
    write("footer.svg", svg)


if __name__ == "__main__":
    header(); dimensions(); skills(); about()
    section("01", "WHO AM I", COR)
    section("02", "DIMENSIONS 3D · 4D · 5D", PUR)
    section("03", "TECH STACK", BLU)
    section("04", "LIVE STATS", MINT)
    section("05", "CONTRIBUTIONS", ORG)
    footer()
