#!/usr/bin/env python3
"""Generates the GitHub stats SVGs in metrics/ from the GraphQL API.

Needs GITHUB_TOKEN (the built-in Actions token is enough) and LOGIN.
Set METRICS_SAMPLE=1 to render with random sample data for local preview only.
"""
import json, math, os, random, sys, urllib.request
from datetime import date, timedelta

OUT = os.environ.get("METRICS_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "metrics"))
os.makedirs(OUT, exist_ok=True)
LOGIN = os.environ.get("LOGIN", "PrathamShrestha69")

BG, BAR, LINE = "#0d1117", "#161b22", "#30363d"
TXT, MUTED, DIM = "#e6edf3", "#8b949e", "#6e7681"
GREEN, CYAN, PURPLE, ORANGE, YEL, RED = "#3fb950", "#58a6ff", "#bc8cff", "#f78166", "#d29922", "#ff7b72"
MONO = "'Fira Code','JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

QUERY = """
query($login:String!){ user(login:$login){
  followers{totalCount} createdAt
  repositories(ownerAffiliations:OWNER,isFork:false,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){
    totalCount
    nodes{ stargazerCount languages(first:8,orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name color } } } } }
  pullRequests{totalCount} issues{totalCount}
  contributionsCollection{ totalCommitContributions
    contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount weekday } } } }
} }"""


def fetch():
    if os.environ.get("METRICS_SAMPLE"):
        return sample()
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
                                 headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit("GraphQL error: " + json.dumps(data["errors"]))
    return data["data"]["user"]


def sample():
    random.seed(3)
    start = date.today() - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    weeks, d = [], start
    while d <= date.today():
        days = []
        for _ in range(7):
            c = 0 if d > date.today() or random.random() < .45 else int(random.expovariate(.25))
            days.append({"date": d.isoformat(), "contributionCount": c, "weekday": (d.weekday() + 1) % 7})
            d += timedelta(days=1)
        weeks.append({"contributionDays": days})
    langs = [("JavaScript", "#f1e05a", 5200), ("TypeScript", "#3178c6", 3100), ("HTML", "#e34c26", 1400), ("CSS", "#563d7c", 900), ("Python", "#3572A5", 500), ("Java", "#b07219", 300)]
    return {"followers": {"totalCount": 12}, "createdAt": "2023-01-01T00:00:00Z",
            "repositories": {"totalCount": 59, "nodes": [{"stargazerCount": 4, "languages": {"edges": [{"size": s, "node": {"name": n, "color": c}} for n, c, s in langs]}}]},
            "pullRequests": {"totalCount": 14}, "issues": {"totalCount": 3},
            "contributionsCollection": {"totalCommitContributions": 480, "contributionCalendar": {"totalContributions": 640, "weeks": weeks}}}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;")


def n1(x):
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">'
            f'<rect width="{w}" height="{h}" rx="12" fill="{BG}" stroke="{LINE}" stroke-width="1.5"/>'
            f'<text x="24" y="34" font-family="{MONO}" font-size="14"><tspan fill="{GREEN}">pratham@shrestha</tspan><tspan fill="{TXT}">:</tspan><tspan fill="{CYAN}">~</tspan><tspan fill="{TXT}">$ </tspan><tspan fill="{TXT}">{esc(label)}</tspan></text>'
            f'<line x1="24" x2="{w-24}" y1="48" y2="48" stroke="{LINE}"/>{body}</svg>')


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"{name:20s} {len(content)/1024:6.1f} KB")


def mix(hexc, f):
    r, g, b = int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16)
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


def days_of(u):
    return [d for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]


def streaks(days):
    best = cur = 0
    for d in days:
        cur = cur + 1 if d["contributionCount"] > 0 else 0
        best = max(best, cur)
    now = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            now += 1
        elif d is days[-1] or d["date"] >= (date.today() - timedelta(days=1)).isoformat():
            continue
        else:
            break
    return best, now


# ------------------------------------------------------------ isocalendar
def isocalendar(u):
    cal = u["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    W, H, c, maxh = 1200, 600, 12.0, 105.0
    mx = max([d["contributionCount"] for w in weeks for d in w["contributionDays"]] + [1])
    cx, cy = 560, 190
    kx, ky = c * .866, c * .5

    def P(gx, gy):
        return cx + (gx - gy) * kx, cy + (gx + gy) * ky

    cells = []
    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            cells.append((wi + d["weekday"], wi, d))
    cells.sort(key=lambda t: t[0])
    out = ""
    for order, wi, d in cells:
        gy = d["weekday"]
        cnt = d["contributionCount"]
        lvl = 0 if cnt == 0 else (1 if cnt <= mx * .25 else 2 if cnt <= mx * .5 else 3 if cnt <= mx * .75 else 4)
        h = 1.5 if cnt == 0 else 4 + cnt / mx * maxh
        base = LEVELS[lvl] if lvl else "#1f2630"
        a, b, cc, dd = P(wi, gy), P(wi + 1, gy), P(wi + 1, gy + 1), P(wi, gy + 1)
        up = lambda p: (p[0], p[1] - h)
        top = " ".join(f"{n1(x)},{n1(y)}" for x, y in map(up, (a, b, cc, dd)))
        left = " ".join(f"{n1(x)},{n1(y)}" for x, y in (dd, cc, up(cc), up(dd)))
        right = " ".join(f"{n1(x)},{n1(y)}" for x, y in (cc, b, up(b), up(cc)))
        faces = (f'<polygon points="{left}" fill="{mix(base, .62)}"/><polygon points="{right}" fill="{mix(base, .8)}"/>'
                 f'<polygon points="{top}" fill="{base}"/>')
        if cnt == 0:
            out += faces
        else:
            bx, by = cc
            t = .3 + wi * .035 + gy * .01
            out += (f'<g transform="translate({n1(bx)} {n1(by)})"><g><animateTransform attributeName="transform" type="scale" from="1 0.02" to="1 1" begin="{t:.2f}s" dur=".6s" fill="freeze"/>'
                    f'<g transform="translate({n1(-bx)} {n1(-by)})">{faces}</g></g></g>')
    best, now = streaks(days_of(u))
    best_day = max(days_of(u), key=lambda d: d["contributionCount"])
    stats = [(f'{cal["totalContributions"]}', "contributions in the last year", GREEN),
             (f'{best_day["contributionCount"]}', f'best day · {best_day["date"]}', CYAN),
             (f'{best} days', "longest streak", ORANGE), (f'{now} days', "current streak", PURPLE)]
    txt = ""
    for i, (v, l, col) in enumerate(stats):
        y = 120 + i * 92
        txt += (f'<text x="48" y="{y}" font-family="{MONO}" font-size="40" font-weight="700" fill="{col}">{esc(v)}</text>'
                f'<text x="48" y="{y+26}" font-family="{MONO}" font-size="14" fill="{MUTED}">{esc(l)}</text>')
    write("isocalendar.svg", svg(W, H, txt + out, "gh isocalendar --full-year"))


# --------------------------------------------------------------- overview
def overview(u):
    cc = u["contributionsCollection"]
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    yrs = max(0, date.today().year - int(u["createdAt"][:4]))
    items = [(cc["contributionCalendar"]["totalContributions"], "contributions · last year", GREEN),
             (cc["totalCommitContributions"], "commits · last year", CYAN),
             (u["pullRequests"]["totalCount"], "pull requests", PURPLE),
             (u["issues"]["totalCount"], "issues opened", ORANGE),
             (stars, "stars earned", YEL),
             (u["repositories"]["totalCount"], "public repositories", GREEN),
             (u["followers"]["totalCount"], "followers", CYAN),
             (yrs, "years on GitHub", PURPLE)]
    out = ""
    for i, (v, l, col) in enumerate(items):
        x, y = 24 + (i % 4) * 293, 70 + (i // 4) * 120
        out += (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".5s" begin="{.1+i*.1}s" fill="freeze"/>'
                f'<rect x="{x}" y="{y}" width="278" height="104" rx="10" fill="{BAR}" stroke="{LINE}"/>'
                f'<text x="{x+20}" y="{y+56}" font-family="{MONO}" font-size="38" font-weight="700" fill="{col}">{v}</text>'
                f'<text x="{x+20}" y="{y+84}" font-family="{MONO}" font-size="13" fill="{MUTED}">{l}</text></g>')
    write("overview.svg", svg(1200, 320, out, "gh overview"))


# -------------------------------------------------------------- languages
def languages(u):
    tot = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            nm = e["node"]["name"]
            t = tot.setdefault(nm, [0, e["node"]["color"] or "#8b949e"])
            t[0] += e["size"]
    top = sorted(tot.items(), key=lambda kv: -kv[1][0])[:6]
    total = sum(v[0] for _, v in top) or 1
    x, out, bar = 24, "", ""
    for i, (nm, (sz, col)) in enumerate(top):
        wd = 552 * sz / total
        bar += (f'<rect x="{n1(x)}" y="72" width="{n1(max(wd-2,1))}" height="16" rx="3" fill="{col}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" dur=".4s" begin="{.2+i*.12}s" fill="freeze"/></rect>')
        x += wd
        y = 130 + i * 30
        out += (f'<circle cx="34" cy="{y-5}" r="6" fill="{col}"/><text x="52" y="{y}" font-family="{MONO}" font-size="15" fill="{TXT}">{esc(nm)}</text>'
                f'<text x="576" y="{y}" text-anchor="end" font-family="{MONO}" font-size="15" fill="{MUTED}">{100*sz/total:.1f}%</text>')
    write("languages.svg", svg(600, 330, bar + out, "gh languages --top 6"))


# ----------------------------------------------------------------- habits
def habits(u):
    days = days_of(u)
    names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    sums = [0] * 7
    for d in days:
        sums[d["weekday"]] += d["contributionCount"]
    mx = max(sums + [1])
    out = ""
    for i, v in enumerate(sums):
        h = 150 * v / mx
        x = 40 + i * 76
        out += (f'<rect x="{x}" y="{240-h:.1f}" width="46" height="{h:.1f}" rx="4" fill="{GREEN if v == max(sums) else CYAN}" opacity=".9">'
                f'<animate attributeName="height" from="0" to="{h:.1f}" dur=".7s" begin="{.1+i*.08}s" fill="freeze"/>'
                f'<animate attributeName="y" from="240" to="{240-h:.1f}" dur=".7s" begin="{.1+i*.08}s" fill="freeze"/></rect>'
                f'<text x="{x+23}" y="262" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">{names[i]}</text>'
                f'<text x="{x+23}" y="{232-h:.1f}" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{DIM}">{v}</text>')
    busiest = names[sums.index(max(sums))]
    active = sum(1 for d in days if d["contributionCount"] > 0)
    out += (f'<text x="24" y="304" font-family="{MONO}" font-size="14" fill="{MUTED}">busiest day <tspan fill="{GREEN}">{busiest}</tspan>'
            f'  ·  active <tspan fill="{CYAN}">{active}</tspan> of {len(days)} days</text>')
    write("habits.svg", svg(600, 330, out, "gh habits --weekday"))


# ----------------------------------------------------------- achievements
def achievements(u):
    cc = u["contributionsCollection"]
    best, _ = streaks(days_of(u))
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    items = [("Repositories", u["repositories"]["totalCount"], (5, 20, 50)), ("Stars", stars, (1, 10, 50)),
             ("Followers", u["followers"]["totalCount"], (1, 10, 50)), ("Commits", cc["totalCommitContributions"], (50, 250, 1000)),
             ("Pull requests", u["pullRequests"]["totalCount"], (1, 10, 50)), ("Best streak", best, (3, 7, 30))]
    tiers = [("—", "#484f58"), ("Bronze", "#cd7f32"), ("Silver", "#c0c8d0"), ("Gold", "#ffd33d")]
    out = ""
    for i, (name, v, th) in enumerate(items):
        lvl = sum(1 for t in th if v >= t)
        tn, tc = tiers[lvl]
        x = 24 + i * 192
        out += (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".5s" begin="{.1+i*.12}s" fill="freeze"/>'
                f'<rect x="{x}" y="70" width="180" height="180" rx="10" fill="{BAR}" stroke="{LINE}"/>'
                f'<circle cx="{x+90}" cy="130" r="38" fill="none" stroke="{tc}" stroke-width="5"/>'
                f'<text x="{x+90}" y="140" text-anchor="middle" font-family="{MONO}" font-size="26" font-weight="700" fill="{TXT}">{v}</text>'
                f'<text x="{x+90}" y="206" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{TXT}">{name}</text>'
                f'<text x="{x+90}" y="230" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{tc}">{tn}</text></g>')
    write("achievements.svg", svg(1200, 280, out, "gh achievements"))


if __name__ == "__main__":
    u = fetch()
    isocalendar(u); overview(u); languages(u); habits(u); achievements(u)
