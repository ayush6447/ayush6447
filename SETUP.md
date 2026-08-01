# Setup

This is a GitHub *profile* README: it only renders on your profile if it
lives in a repo named exactly `ayush6447/ayush6447` (public).

## First-time setup

1. Create that repo if it doesn't exist yet, and push everything in this
   folder to its `main` branch.
2. In the repo's **Settings → Actions → General → Workflow permissions**,
   set it to **"Read and write permissions"** — the daily action needs to
   `git push` the regenerated SVGs back to the repo.
3. Run the workflow once by hand (**Actions tab → "update stats" →
   Run workflow**) so `hd-*.svg`, `streak.svg`, `langs.svg`, and `year.svg`
   exist before anyone views the profile. After that it runs on its own,
   once a day.

## Running it locally (optional)

```bash
pip install fonttools brotli
python scripts/generate_headings.py
GH_TOKEN=<a token with public read access> GH_USERNAME=ayush6447 python scripts/generate_stats.py
```

## Files

- `README.md` — the profile page itself
- `scripts/generate_headings.py` — draws `hd-about.svg`, `hd-stack.svg`, etc.
- `scripts/generate_stats.py` — pulls contribution/language data and draws
  `streak.svg`, `langs.svg`, `year.svg`
- `scripts/fontutil.py` — subsets JetBrains Mono per-graphic and inlines it
  as base64, so every SVG is self-contained
- `scripts/fonts/` — the source JetBrains Mono TTFs the subsetter reads from
- `.github/workflows/stats.yml` — the daily cron that regenerates and commits

## Tweaking

- Accent color (`#a259ff`) and dim color (`#6e6e80`) are set once at the top
  of both `generate_headings.py` and `generate_stats.py`.
- Add/remove projects, socials, or stack entries directly in `README.md` —
  those parts are static text, not generated.
- `year.svg`'s bucket thresholds are percentile-based off your own active
  days, so the ramp stays meaningful regardless of how active you are.
