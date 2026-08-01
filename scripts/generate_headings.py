"""
Draws the section headings as SVGs (e.g. "about", "stack", "projects").
GitHub strips <style> blocks and custom CSS out of README markdown, so a
plain <h2>about</h2> would render in the viewer's default font. Baking the
heading into an SVG with the font embedded is the only way to keep this
page's own typeface on it.
"""
import os
from fontutil import font_face_css

OUT_DIR = os.path.join(os.path.dirname(__file__), "..")
ACCENT = "#a259ff"
DIM = "#6e6e80"

HEADINGS = {
    "hd-about": "about",
    "hd-stack": "stack",
    "hd-projects": "projects",
    "hd-stats": "stats",
    "hd-about-this-page": "about this page",
}

TITLE_TEXT = "hi, i'm ayush kumar singh"
TITLE_SUBTEXT = "cse student  ·  ai/ml + flutter  ·  jharkhand, india"

FONT_FAMILY = "JBM-HD"


def make_title_svg(label: str, subtext: str) -> str:
    font_size = 30
    letter_spacing = 2
    sub_font_size = 14
    sub_letter_spacing = 3
    width = 620

    css = font_face_css(FONT_FAMILY, label + label.upper() + subtext + subtext.upper(), bold=True)

    title_w = len(label) * (font_size * 0.6 + letter_spacing)
    sub_w = len(subtext) * (sub_font_size * 0.6 + sub_letter_spacing)
    height = 92

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>{css}
    .ti-label {{ font-family:'{FONT_FAMILY}',monospace; font-size:{font_size}px; font-weight:700; letter-spacing:{letter_spacing}px; fill:{ACCENT}; }}
    .ti-sub {{ font-family:'{FONT_FAMILY}',monospace; font-size:{sub_font_size}px; font-weight:700; letter-spacing:{sub_letter_spacing}px; fill:{DIM}; text-transform:uppercase; }}
  </style>
  <text x="{width/2:.1f}" y="42" text-anchor="middle" class="ti-label">{label}</text>
  <text x="{width/2:.1f}" y="72" text-anchor="middle" class="ti-sub">{subtext}</text>
</svg>"""


def make_heading_svg(label: str) -> str:
    font_size = 20
    letter_spacing = 3
    padding_left = 2
    width = 620
    height = 36
    css = font_face_css(FONT_FAMILY, label + label.upper(), bold=True)

    text_w = len(label) * (font_size * 0.6 + letter_spacing)
    rule_x = padding_left + text_w + 14
    rule_end = width - 2

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>{css}
    .hd-label {{ font-family:'{FONT_FAMILY}',monospace; font-size:{font_size}px; font-weight:700; letter-spacing:{letter_spacing}px; fill:{ACCENT}; text-transform:lowercase; }}
    .hd-rule {{ stroke:{DIM}; stroke-width:1; opacity:0.35; }}
  </style>
  <text x="{padding_left}" y="23" class="hd-label">{label}</text>
  <line x1="{rule_x:.1f}" y1="20" x2="{rule_end}" y2="20" class="hd-rule" />
</svg>"""


def main():
    for filename, label in HEADINGS.items():
        svg = make_heading_svg(label)
        out_path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(out_path, "w") as f:
            f.write(svg)
        print(f"wrote {out_path}")

    title_svg = make_title_svg(TITLE_TEXT, TITLE_SUBTEXT)
    title_path = os.path.join(OUT_DIR, "hd-title.svg")
    with open(title_path, "w") as f:
        f.write(title_svg)
    print(f"wrote {title_path}")


if __name__ == "__main__":
    main()
