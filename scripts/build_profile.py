#!/usr/bin/env python3
"""Renders the profile card as two self-contained SVGs (dark + light).

The wordmark is outlined path data (no web font, so nothing can be blocked or
fall back), the ASCII portrait is locked to a fixed grid with textLength, and
everything else is system type. Numbers come from the GitHub API.

    GITHUB_TOKEN=... python scripts/build_profile.py
    python scripts/build_profile.py --stats assets/stats.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wordmark import CAP_TOP, D as WORDMARK_D, DESCENDER, WIDTH as WORDMARK_W  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

LOGIN = "mitomaniaco"
TOP_REPO = "cobblemon-companion"
LANG_COUNT = 3

W, H = 880, 620
PAD = 56

# ---------------------------------------------------------------- github api


def api(url: str, token: str | None) -> dict:
    req = Request(url, headers={"Accept": "application/vnd.github+json",
                                "User-Agent": "profile-card"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=30) as r:
        return json.load(r)


def api_count(query: str, token: str | None) -> int:
    data = api(f"https://api.github.com/search/issues?q={quote_plus(query)}&per_page=1", token)
    return int(data.get("total_count", 0))


def gql(query: str, token: str | None) -> dict:
    req = Request("https://api.github.com/graphql",
                  data=json.dumps({"query": query}).encode(),
                  headers={"Authorization": f"Bearer {token}",
                           "Content-Type": "application/json",
                           "User-Agent": "profile-card"})
    with urlopen(req, timeout=30) as r:
        return json.load(r)


def elapsed(start: date, end: date) -> tuple[int, int, int]:
    import calendar

    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day
    if days < 0:
        months -= 1
        prev_month = end.month - 1 or 12
        prev_year = end.year if end.month > 1 else end.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12
    return years, months, days


def human(n: int) -> str:
    return f"{n:,}"


def collect(token: str | None) -> dict:
    user = api(f"https://api.github.com/users/{LOGIN}", token)

    repos, page = [], 1
    while True:
        chunk = api(f"https://api.github.com/users/{LOGIN}/repos?per_page=100&page={page}"
                    "&type=owner&sort=pushed", token)
        if not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1

    own = [r for r in repos if not r["fork"] and not r["archived"]]
    langs: dict[str, int] = {}
    for r in own:
        try:
            for name, size in api(
                    f"https://api.github.com/repos/{LOGIN}/{r['name']}/languages", token).items():
                langs[name] = langs.get(name, 0) + int(size)
        except Exception:
            continue
    total = sum(langs.values()) or 1
    lang_txt = ", ".join(f"{n} {v * 100 // total}%"
                         for n, v in sorted(langs.items(), key=lambda kv: -kv[1])[:LANG_COUNT])

    prev = {}
    try:
        prev = json.loads((ASSETS / "stats.json").read_text())
    except Exception:
        pass

    contributions = prev.get("contributions", 0)
    try:
        g = gql('query{user(login:"%s"){contributionsCollection{contributionCalendar'
                '{totalContributions}}}}' % LOGIN, token)
        contributions = g["data"]["user"]["contributionsCollection"][
            "contributionCalendar"]["totalContributions"]
    except Exception:
        pass

    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")).date()
    y, m, d = elapsed(created, date.today())

    return {
        "uptime": f"{y}y {m}m",
        "uptime_long": f"{y} years, {m} months, {d} days",
        "languages": lang_txt,
        "repos": len(own),
        "stars": sum(r["stargazers_count"] for r in own),
        "forks": sum(r["forks_count"] for r in own),
        "followers": user["followers"],
        "prs": api_count(f"author:{LOGIN} type:pr", token),
        "issues": api_count(f"author:{LOGIN} type:issue", token),
        "contributions": contributions,
        "top": TOP_REPO,
        "generated": date.today().isoformat(),
    }


# ------------------------------------------------------------------- layout

THEMES = {
    "dark": dict(bg="#08090c", fg="#e6edf3", muted="#98a3b1", dim="#5c6673",
                 faint="#46505c", accent="#39d5e8", rule="#22282f", art="#dfe9f3",
                 art_opacity=".92"),
    "light": dict(bg="#ffffff", fg="#0d1117", muted="#4c5763", dim="#6e7681",
                  faint="#8b949e", accent="#0e7490", rule="#d8dee4", art="#1f2328",
                  art_opacity=".60"),
}

ART_SIZE = 11.5
ART_LH = 13.8
ART_CHAR_W = 6.9

KICKER_Y = 78
MARK_SIZE = 74
MARK_BASE = 208
SUB_Y = 240
RULE_Y = 264
LEDE_SIZE = 14
LEDE_LH = 23
LEDE_Y = 296
WORK_Y = 400
WORK_LH = 28
FIG_Y = 592

LEDE = [
    [("I build software that removes friction — ", False), ("usually my own.", True)],
    [("Offline by default, no cloud tax, and the tool never", False)],
    [("acts for you: it hands you the decision.", False)],
]

WORK = [
    ("harvey/", "Prospecting that never sends the message for you."),
    ("cobblemon-companion/", "A planner that reads your save."),
    ("portfolio/", "Static, fast, no framework tax."),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_theme(stats: dict, name: str, portrait: str) -> str:
    t = THEMES[name]
    lines = portrait.split("\n")
    cols = max(len(l) for l in lines)
    art_len = cols * ART_CHAR_W
    art_x = 470
    art_top = (H - len(lines) * ART_LH) / 2
    art_y = art_top + ART_SIZE
    art_h = len(lines) * ART_LH

    art = "\n".join(
        f'<text x="0" y="{i * ART_LH:.1f}" class="a" textLength="{art_len:.1f}" '
        f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{esc(l.ljust(cols))}</text>'
        for i, l in enumerate(lines))

    scale = MARK_SIZE / 1000

    fig = " &nbsp; ".join(
        f'<tspan fill="{t["muted"]}">{esc(v)}</tspan> {esc(k)}'
        for v, k in (("{}".format(human(stats["contributions"])), "contributions"),
                     (human(stats["prs"]), "pull requests"),
                     (human(stats["issues"]), "issues"),
                     (stats["uptime"], "on github"),
                     (human(stats["stars"]), "stars"),
                     (human(stats["followers"]), "followers")))

    work = "\n".join(
        f'<text x="{PAD}" y="{WORK_Y + i * WORK_LH}" class="pn">{esc(n)}</text>'
        f'<text x="{PAD + 168}" y="{WORK_Y + i * WORK_LH}" class="pd">{esc(d)}</text>'
        for i, (n, d) in enumerate(WORK))

    lede_rows = "\n".join(
        f'<text x="{PAD}" y="{LEDE_Y + i * LEDE_LH}" class="l">'
        + "".join(
            f'<tspan{" font-weight=\"500\"" if bold else ""}'
            f'{" fill=" + chr(34) + t["fg"] + chr(34) if bold else ""}>{esc(txt)}</tspan>'
            for txt, bold in row)
        + "</text>"
        for i, row in enumerate(LEDE))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Requiem — ascii portrait and a typographic profile card">
<title>Requiem — local-first software</title>
<style>
  text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  .k  {{ font-size:10px; letter-spacing:.22em; font-weight:600; fill:{t["accent"]}; }}
  .k2 {{ font-size:10px; letter-spacing:.22em; fill:{t["dim"]}; }}
  .s  {{ font-size:12px; letter-spacing:.3em; fill:{t["faint"]}; }}
  .l  {{ font-size:{LEDE_SIZE}px; fill:{t["muted"]}; }}
  .pn {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
         font-size:12px; fill:{t["fg"]}; }}
  .pd {{ font-size:11.5px; fill:{t["dim"]}; }}
  .f  {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
         font-size:10.5px; fill:{t["dim"]}; letter-spacing:.03em; }}
  .a  {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
         font-size:{ART_SIZE}px; fill:{t["art"]}; opacity:{t["art_opacity"]}; }}
</style>
<rect width="{W}" height="{H}" fill="{t["bg"]}"/>
<g transform="translate({art_x:.1f},{art_y:.1f})">{art}</g>
<defs>
  <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{t["bg"]}" stop-opacity="1"/>
    <stop offset="1" stop-color="{t["bg"]}" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect x="{art_x - 40:.1f}" y="0" width="230" height="{H}" fill="url(#fade)"/>
<text x="{PAD}" y="{KICKER_Y}" class="k">MITOMANIACO</text>
<text x="{PAD + 118}" y="{KICKER_Y}" class="k2">· BRASIL · UTC&#8722;3</text>
<path transform="translate({PAD},{MARK_BASE}) scale({scale})" d="{WORDMARK_D}" fill="{t["fg"]}"/>
<text x="{PAD + 3}" y="{SUB_Y}" class="s">LOCAL&#8722;FIRST SOFTWARE</text>
<rect x="{PAD}" y="{RULE_Y}" width="330" height="1" fill="{t["rule"]}"/>
{lede_rows}
{work}
<text x="{PAD}" y="{FIG_Y}" class="f">{fig}</text>
<desc>ASCII portrait on the right; wordmark {esc(stats["top"])}; {esc(stats["uptime_long"])}</desc>
</svg>
"""


def main() -> int:
    if "--stats" in sys.argv:
        stats = json.loads(Path(sys.argv[sys.argv.index("--stats") + 1]).read_text())
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
        if not token:
            try:
                import subprocess
                token = subprocess.run(["gh", "auth", "token"], capture_output=True,
                                       text=True, timeout=10).stdout.strip()
            except Exception:
                token = ""
        try:
            stats = collect(token)
        except Exception as exc:
            print(f"collect failed: {exc}", file=sys.stderr)
            return 1

    portrait = (ASSETS / "portrait.txt").read_text(encoding="utf-8").rstrip("\n")
    for theme in ("dark", "light"):
        (ASSETS / f"card-{theme}.svg").write_text(
            render_theme(stats, theme, portrait), encoding="utf-8")
    (ASSETS / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
