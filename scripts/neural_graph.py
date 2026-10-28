import json, os, sys, urllib.request, random
from datetime import datetime

USER = os.environ.get("GH_USER", "HarshitaShakya")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT", "neural-graph.svg")

QUERY = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}"""

def fetch():
    if os.environ.get("MOCK"):
        random.seed(3)
        weeks = [{"contributionDays": [{"date": "2026-01-01", "weekday": d,
                  "contributionCount": random.choice([0, 0, 0, 1, 2, 4, 7, 12])}
                 for d in range(7)]} for _ in range(53)]
        return {"totalContributions": 1234, "weeks": weeks}
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

cal = fetch()
CELL, PAD_X, PAD_TOP = 14, 30, 62
cols = len(cal["weeks"])
W = PAD_X * 2 + cols * CELL
H = PAD_TOP + 7 * CELL + 40

nodes = []  # (x, y, count)
for wi, w in enumerate(cal["weeks"]):
    for d in w["contributionDays"]:
        x = PAD_X + wi * CELL + CELL / 2
        y = PAD_TOP + d["weekday"] * CELL + CELL / 2
        nodes.append((x, y, d["contributionCount"]))

mx = max((n[2] for n in nodes), default=1) or 1
active = [n for n in nodes if n[2] > 0]

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
 '<defs><filter id="g" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
 '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
 f'<rect width="{W}" height="{H}" rx="14" fill="#0a0f0d"/>',
 f'<text x="{PAD_X}" y="30" font-family="JetBrains Mono,Consolas,monospace" font-size="14" fill="#00ff41">'
 f'&gt;&gt;&gt; neural_activity.fire()</text>',
 f'<text x="{PAD_X}" y="48" font-family="JetBrains Mono,Consolas,monospace" font-size="11" fill="#5f8f6f">'
 f'{cal["totalContributions"]} activations in the last year</text>']

# dormant neurons
for x, y, c in nodes:
    if c == 0:
        svg.append(f'<circle cx="{x}" cy="{y}" r="1.4" fill="#16382a"/>')

# synapses between nearby active neurons (chronological neighbours, short gaps)
for i in range(len(active) - 1):
    a, b = active[i], active[i + 1]
    if abs(a[0] - b[0]) <= CELL * 2.2:
        op = 0.25 + 0.5 * min(a[2], b[2]) / mx
        svg.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" '
                   f'stroke="#00ff41" stroke-opacity="{op:.2f}" stroke-width="1"/>')

# firing neurons
for i, (x, y, c) in enumerate(active):
    r = 2.2 + 3.6 * (c / mx) ** 0.6
    col = "#00ff41" if c > mx * 0.5 else "#00d9ff" if c > mx * 0.2 else "#1e90ff"
    dur = 2 + (i % 5) * 0.4
    begin = (i % 17) * 0.25
    svg.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{col}" filter="url(#g)">'
               f'<animate attributeName="opacity" values="1;0.45;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
               f'</circle>')

svg.append('</svg>')
open(OUT, "w").write("\n".join(svg))
print("wrote", OUT, len(active), "active nodes")
