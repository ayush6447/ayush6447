"""
Pulls live data straight from the GitHub GraphQL + REST API and renders it
into three self-contained SVGs:

  streak.svg  - current streak & longest streak, from the contribution calendar
  langs.svg   - top languages by bytes, and by repo count, across public repos
  year.svg    - the last 371 days, one character per day, using the ramp
                ": + # @" (quiet to loud) based on that day's commit count

Requires env vars GH_TOKEN (a token with public read access; the default
GITHUB_TOKEN from Actions is enough) and GH_USERNAME.
"""
import os
import sys
import json
import datetime
import urllib.request

from fontutil import font_face_css

GH_TOKEN = os.environ["GH_TOKEN"]
GH_USERNAME = os.environ["GH_USERNAME"]
OUT_DIR = os.path.join(os.path.dirname(__file__), "..")

ACCENT = "#a259ff"
PALETTE = ["#a259ff", "#59c9ff", "#59ffb0", "#ffcb59", "#ff7a59", "#ff59c8"]
FG = "#e6e6e6"
DIM = "#6e6e80"
BG = "none"
FONT_FAMILY = "JBM-ST"

RAMP = " :+#@"  # index 0..4, quiet -> loud


def gh_graphql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {GH_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": GH_USERNAME,
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def gh_rest(path: str):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": GH_USERNAME,
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


# ---------------------------------------------------------------------------
# data fetching
# ---------------------------------------------------------------------------

CONTRIB_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


def fetch_daily_contributions():
    data = gh_graphql(CONTRIB_QUERY, {"login": GH_USERNAME})
    weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))
    days.sort(key=lambda x: x[0])
    return days


def fetch_repo_languages():
    """Returns dict: language -> (total_bytes, repo_count), public repos only."""
    repos = []
    page = 1
    while True:
        batch = gh_rest(f"/users/{GH_USERNAME}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    totals = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        langs = gh_rest(f"/repos/{GH_USERNAME}/{repo['name']}/languages")
        for lang, byte_count in langs.items():
            bytes_total, repo_count = totals.get(lang, (0, 0))
            totals[lang] = (bytes_total + byte_count, repo_count + 1)
    return totals


# ---------------------------------------------------------------------------
# streak.svg
# ---------------------------------------------------------------------------

def compute_streaks(days):
    today = datetime.date.today()
    by_date = {datetime.date.fromisoformat(d): c for d, c in days}

    # current streak: walk backwards from today (allow today to be empty so
    # far, start from yesterday if today has 0 so far)
    current = 0
    cursor = today
    if by_date.get(cursor, 0) == 0:
        cursor -= datetime.timedelta(days=1)
    while by_date.get(cursor, 0) > 0:
        current += 1
        cursor -= datetime.timedelta(days=1)

    # longest streak across the whole window
    longest = 0
    run = 0
    for d, c in days:
        if c > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    return current, longest


def render_streak_svg(current: int, longest: int) -> str:
    label = f"CURRENT STREAK{longest}LONGEST STREAK{current} days{longest} days"
    css = font_face_css(FONT_FAMILY, label, bold=True)
    width, height = 620, 90

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>{css}
    .st-num {{ font-family:'{FONT_FAMILY}',monospace; font-size:40px; font-weight:700; fill:{ACCENT}; }}
    .st-lbl {{ font-family:'{FONT_FAMILY}',monospace; font-size:13px; letter-spacing:2px; fill:{DIM}; text-transform:uppercase; }}
  </style>
  <text x="0" y="50" class="st-num">{current} days</text>
  <text x="0" y="72" class="st-lbl">current streak</text>

  <text x="320" y="50" class="st-num">{longest} days</text>
  <text x="320" y="72" class="st-lbl">longest streak</text>
</svg>"""


# ---------------------------------------------------------------------------
# langs.svg
# ---------------------------------------------------------------------------

def render_langs_svg(lang_totals: dict, top_n: int = 6) -> str:
    by_bytes = sorted(lang_totals.items(), key=lambda kv: kv[1][0], reverse=True)[:top_n]
    by_repos = sorted(lang_totals.items(), key=lambda kv: kv[1][1], reverse=True)[:top_n]

    max_bytes = max((v[0] for _, v in by_bytes), default=1)
    max_repos = max((v[1] for _, v in by_repos), default=1)

    all_text = "by bytesby repo" + "".join(k for k, _ in by_bytes) + "".join(k for k, _ in by_repos)
    css = font_face_css(FONT_FAMILY, all_text, bold=False)

    width, height = 620, 30 + max(len(by_bytes), len(by_repos)) * 24 + 10
    bar_max_w = 230

    def column(items, max_val, x_offset, title):
        rows = [f'<text x="{x_offset}" y="18" class="lg-title">{title}</text>']
        y = 40
        for i, (lang, (b, r)) in enumerate(items):
            val = b if title == "by bytes" else r
            w = max(4, (val / max_val) * bar_max_w)
            color = PALETTE[i % len(PALETTE)]
            rows.append(f'<text x="{x_offset}" y="{y}" class="lg-lbl">{lang}</text>')
            rows.append(f'<rect x="{x_offset}" y="{y+6}" width="{w:.1f}" height="6" rx="3" fill="{color}" opacity="0.85"/>')
            y += 24
        return "\n".join(rows)

    left = column(by_bytes, max_bytes, 0, "by bytes")
    right = column(by_repos, max_repos, 320, "by repo")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>{css}
    .lg-title {{ font-family:'{FONT_FAMILY}',monospace; font-size:13px; letter-spacing:2px; fill:{DIM}; text-transform:uppercase; }}
    .lg-lbl {{ font-family:'{FONT_FAMILY}',monospace; font-size:13px; fill:{FG}; }}
  </style>
  {left}
  {right}
</svg>"""


# ---------------------------------------------------------------------------
# year.svg
# ---------------------------------------------------------------------------

def render_year_svg(days) -> str:
    counts = [c for _, c in days]
    nonzero = sorted(c for c in counts if c > 0)
    if nonzero:
        # thresholds at the 33rd/66th/90th percentile of active days
        def pct(p):
            idx = min(len(nonzero) - 1, int(len(nonzero) * p))
            return nonzero[idx]
        t1, t2, t3 = pct(0.33), pct(0.66), pct(0.9)
    else:
        t1 = t2 = t3 = 1

    def char_for(c):
        if c == 0:
            return RAMP[0]
        if c <= t1:
            return RAMP[1]
        if c <= t2:
            return RAMP[2]
        if c <= t3:
            return RAMP[3]
        return RAMP[4]

    chars = "".join(char_for(c) for _, c in days)
    per_row = 53
    rows = [chars[i:i + per_row] for i in range(0, len(chars), per_row)]

    css = font_face_css(FONT_FAMILY, chars + RAMP, bold=False)
    font_size = 11
    line_height = 14
    width = 620
    height = 20 + len(rows) * line_height + 10

    text_rows = []
    for i, row in enumerate(rows):
        y = 20 + i * line_height
        text_rows.append(f'<text x="0" y="{y}" class="yr-row">{row}</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>{css}
    .yr-row {{ font-family:'{FONT_FAMILY}',monospace; font-size:{font_size}px; fill:{ACCENT}; white-space:pre; }}
  </style>
  {chr(10).join(text_rows)}
</svg>"""


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def write(name, content):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w") as f:
        f.write(content)
    print(f"wrote {path}")


def main():
    days = fetch_daily_contributions()
    current, longest = compute_streaks(days)
    write("streak.svg", render_streak_svg(current, longest))
    write("year.svg", render_year_svg(days))

    lang_totals = fetch_repo_languages()
    write("langs.svg", render_langs_svg(lang_totals))


if __name__ == "__main__":
    main()
