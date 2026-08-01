"""
Shared helper: subset JetBrains Mono down to only the characters a given
SVG needs, then return it as a base64 string ready to inline in an
@font-face rule. Keeps every generated SVG tiny and self-contained, so
nothing in the README ever depends on a third-party font CDN.
"""
import base64
import io
import os
import subprocess
import tempfile

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
REGULAR = os.path.join(FONT_DIR, "JetBrainsMono-Regular.ttf")
BOLD = os.path.join(FONT_DIR, "JetBrainsMono-Bold.ttf")

# advance width baked into JetBrains Mono at 1000 units/em -> 0.600 em/glyph
ADVANCE_EM = 0.6


def subset_font_base64(text: str, bold: bool = False) -> str:
    """Subset the font to the unique characters in `text` and return
    base64-encoded WOFF bytes (small + universally supported in SVG)."""
    src = BOLD if bold else REGULAR
    chars = "".join(sorted(set(text)))
    if not chars.strip():
        chars = " "
    with tempfile.NamedTemporaryFile(suffix=".woff", delete=False) as tmp:
        out_path = tmp.name
    try:
        subprocess.run(
            [
                "fonttools", "subset", src,
                f"--text={chars}",
                f"--output-file={out_path}",
                "--flavor=woff",
                "--layout-features=*",
                "--no-hinting",
            ],
            check=True, capture_output=True,
        )
        with open(out_path, "rb") as f:
            data = f.read()
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)
    return base64.b64encode(data).decode("ascii")


def font_face_css(font_family: str, text: str, bold: bool = False) -> str:
    b64 = subset_font_base64(text, bold=bold)
    return (
        f"@font-face{{font-family:'{font_family}';"
        f"src:url(data:font/woff;base64,{b64}) format('woff');"
        f"font-weight:{'700' if bold else '400'};}}"
    )


def text_width(s: str, font_size: float) -> float:
    """Monospace width estimate using JetBrains Mono's fixed advance."""
    return len(s) * font_size * ADVANCE_EM
