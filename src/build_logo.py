"""Build a LEGO mosaic of the MIRAOMICS logo.

7-row pixel font for the letters; the second O in MIRAOMICS is replaced by a
two-ball molecular symbol in green. Everything else is white. The mosaic lies
flat on the build plate, so the `top` view in the rendered camera set reads
as the logo. Each pixel is one 1x1 plate (3024).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from catalog import color  # noqa: E402
from model import Model    # noqa: E402
from render import Camera, RenderStyle, render_views  # noqa: E402


# 5-wide × 7-tall pixel font, with `I` 1-wide. Rows top-to-bottom.
FONT: dict[str, list[str]] = {
    "M": [
        "X...X",
        "XX.XX",
        "X.X.X",
        "X.X.X",
        "X...X",
        "X...X",
        "X...X",
    ],
    "I": [
        "X",
        "X",
        "X",
        "X",
        "X",
        "X",
        "X",
    ],
    "R": [
        "XXXX.",
        "X...X",
        "X...X",
        "XXXX.",
        "X.X..",
        "X..X.",
        "X...X",
    ],
    "A": [
        ".XXX.",
        "X...X",
        "X...X",
        "XXXXX",
        "X...X",
        "X...X",
        "X...X",
    ],
    "C": [
        ".XXXX",
        "X....",
        "X....",
        "X....",
        "X....",
        "X....",
        ".XXXX",
    ],
    "S": [
        ".XXXX",
        "X....",
        "X....",
        ".XXX.",
        "....X",
        "....X",
        "XXXX.",
    ],
}

# Two-ball molecular symbol replacing the second O. Same 7-row height. Small
# ball on top (3-wide), thin bar in the middle, larger ball on the bottom
# (5-wide) — same proportions as the source logo.
SYMBOL = [
    "..G..",
    ".GGG.",
    "..G..",
    "..G..",
    ".GGG.",
    "GGGGG",
    ".GGG.",
]

# String to render. The 4th character (index 4, 0-based) is the O that gets
# replaced by SYMBOL.
TEXT = "MIRAOMICS"
SYMBOL_INDEX = 4
LETTER_GAP = 1     # studs of white between letters
BORDER = 2         # studs of white border around the whole logo


def _render_grid() -> list[str]:
    """Compose the 7-row character strip with letter gaps and the symbol."""
    rows = ["" for _ in range(7)]
    for i, ch in enumerate(TEXT):
        glyph = SYMBOL if i == SYMBOL_INDEX else FONT[ch]
        for r in range(7):
            if i > 0:
                rows[r] += "." * LETTER_GAP   # white gap between letters
            rows[r] += glyph[r]
    return rows


def build_logo_mosaic() -> Model:
    char_rows = _render_grid()
    inner_w = max(len(r) for r in char_rows)
    inner_h = 7
    total_w = inner_w + 2 * BORDER
    total_h = inner_h + 2 * BORDER

    m = Model(name="miraomics_logo", author="bricklink-automation")

    white = color("white")
    black = color("black")
    green = color("green")

    # Lay 1x1 plates over the full WxH grid. White by default; black where a
    # letter pixel ('X'); green where the symbol pixel ('G').
    for row in range(total_h):
        for col in range(total_w):
            inner_row = row - BORDER
            inner_col = col - BORDER
            c = white
            if 0 <= inner_row < inner_h and 0 <= inner_col < inner_w:
                row_str = char_rows[inner_row]
                if inner_col < len(row_str):
                    ch = row_str[inner_col]
                    if ch == "X":
                        c = black
                    elif ch == "G":
                        c = green

            # Place plate centered at (stud_x, stud_z). We place the logo so
            # that the top of the text is at +Z (further from camera in top
            # view), matching how you'd "read" it from above.
            stud_x = col - total_w / 2 + 0.5
            stud_z = (total_h - 1 - row) - total_h / 2 + 0.5
            m.place("3024", c, stud_x=stud_x, stud_z=stud_z, level=0)

    return m


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    model = build_logo_mosaic()
    ldr = model.write_ldr(out_dir / "miraomics_logo.ldr")
    iof = model.write_io(out_dir / "miraomics_logo.io")
    print(f"{len(model)} parts -> {ldr}, {iof}")

    # Render: a top-down view that reads as the logo plus a 3/4 hero. The
    # mosaic is ~4.4:1 so we use a matching wide image; LDView fits the model
    # to the frame and a square or 16:9 frame would crop the ends.
    cameras = (
        Camera("top",  lat=89.9, lon=0),
        Camera("hero", lat=30,   lon=45),
        Camera("front", lat=15,  lon=0),
    )
    style = RenderStyle(width=2400, height=600)
    views = render_views(ldr, out_dir, cameras=cameras, style=style)
    for v in views:
        print(f"  {v}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("out/logo")
    main(out)
