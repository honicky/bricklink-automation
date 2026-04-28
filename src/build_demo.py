"""End-to-end demo: build a model in Python, render it, export .ldr and .io.

Closes the loop: this is the smallest amount of code that lets an external
caller (CLI / MCP / another script) construct a LEGO model, see it, and hand
the .io file to Studio.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from catalog import color  # noqa: E402
from model import Model    # noqa: E402
from render import render_views  # noqa: E402


def build_rainbow_tower() -> Model:
    """4-brick stack, each a 2x4 in a different color, demonstrating place()."""
    m = Model(name="rainbow_tower", author="bricklink-automation")
    for i, c in enumerate(["red", "yellow", "green", "blue"]):
        m.place("3001", color(c), stud_x=0, stud_z=0, level=i * 3)
    return m


def build_microhouse() -> Model:
    """Tiny 4x4 stud house: brown floor, red walls, white sloped roof.

    Stud grid runs from (-2, -2) to (+1, +1) — a 4-stud square footprint.
    The 4x4 plate is centred at (0,0). Walls run along the perimeter.
    """
    m = Model(name="microhouse", author="bricklink-automation")

    # Floor: 4x4 brown plate centred at origin.
    m.place("3031", color("reddish_brown"), level=0)

    # Walls: a ring of 1x4 bricks around the floor's perimeter, 1 brick tall.
    # Two walls run along X (front + back), two along Z (left + right) and
    # need rotate=1 to align with the Z axis.
    m.place("3010", color("red"), stud_x=0,   stud_z=-2, level=1)              # back
    m.place("3010", color("red"), stud_x=0,   stud_z=+2, level=1)              # front
    m.place("3010", color("red"), stud_x=-2,  stud_z=0,  level=1, rotate=1)    # left
    m.place("3010", color("red"), stud_x=+2,  stud_z=0,  level=1, rotate=1)    # right

    # Roof base: 4x4 white plate sitting on top of the walls (1 brick = 3 plates up).
    m.place("3031", color("white"), level=4)

    # Two 2x4 slopes pointing inward to form a peaked roof. (These would point
    # opposite directions for a real ridge — for a demo we just stack a couple
    # to give a non-trivial silhouette.)
    m.place("3037", color("white"), stud_x=-1, stud_z=0, level=5)
    m.place("3037", color("white"), stud_x=+1, stud_z=0, level=5, rotate=2)

    return m


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, model in [
        ("rainbow_tower", build_rainbow_tower()),
        ("microhouse",    build_microhouse()),
    ]:
        ldr = model.write_ldr(out_dir / f"{name}.ldr")
        io_file = model.write_io(out_dir / f"{name}.io")
        print(f"{name}: {len(model)} parts -> {ldr}, {io_file}")

        # Render all 6 default cameras into a per-model subdir.
        renders = render_views(ldr, out_dir / name)
        print(f"  rendered {len(renders)} views into {renders[0].parent}/")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("out/demo")
    main(out)
