"""Hand-curated tiny parts and colors catalog.

Just enough to build basic models — bricks, plates, tiles, a couple of slopes
and round parts, plus the most common LEGO colors. Pulled from the official
LDraw library at /usr/share/ldraw — every part_id below has a corresponding
.dat file shipped with the `ldraw-parts` package.

To grow this catalog: scrape names from /usr/share/ldraw/parts/*.dat (the
first comment line of each .dat is the human name) or pull from BrickLink's
catalog API later.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PartSpec:
    part_id: str
    name: str
    width_studs: int           # short horizontal dimension
    length_studs: int          # long horizontal dimension
    height_plates: int         # 1 plate = 8 LDU; 1 brick = 3 plates


# A tiny-but-useful starter set. width <= length by convention.
PARTS: dict[str, PartSpec] = {
    # --- bricks (3 plates tall) ---
    "3005": PartSpec("3005", "Brick 1x1",   1, 1, 3),
    "3004": PartSpec("3004", "Brick 1x2",   1, 2, 3),
    "3622": PartSpec("3622", "Brick 1x3",   1, 3, 3),
    "3010": PartSpec("3010", "Brick 1x4",   1, 4, 3),
    "3009": PartSpec("3009", "Brick 1x6",   1, 6, 3),
    "3008": PartSpec("3008", "Brick 1x8",   1, 8, 3),
    "3003": PartSpec("3003", "Brick 2x2",   2, 2, 3),
    "3002": PartSpec("3002", "Brick 2x3",   2, 3, 3),
    "3001": PartSpec("3001", "Brick 2x4",   2, 4, 3),
    "3007": PartSpec("3007", "Brick 2x8",   2, 8, 3),
    # --- plates (1 plate tall) ---
    "3024": PartSpec("3024", "Plate 1x1",   1, 1, 1),
    "3023": PartSpec("3023", "Plate 1x2",   1, 2, 1),
    "3623": PartSpec("3623", "Plate 1x3",   1, 3, 1),
    "3710": PartSpec("3710", "Plate 1x4",   1, 4, 1),
    "3666": PartSpec("3666", "Plate 1x6",   1, 6, 1),
    "3460": PartSpec("3460", "Plate 1x8",   1, 8, 1),
    "3022": PartSpec("3022", "Plate 2x2",   2, 2, 1),
    "3021": PartSpec("3021", "Plate 2x3",   2, 3, 1),
    "3020": PartSpec("3020", "Plate 2x4",   2, 4, 1),
    "3034": PartSpec("3034", "Plate 2x8",   2, 8, 1),
    "3031": PartSpec("3031", "Plate 4x4",   4, 4, 1),
    # --- tiles (1 plate tall, no studs on top) ---
    "3070b": PartSpec("3070b", "Tile 1x1",  1, 1, 1),
    "3069b": PartSpec("3069b", "Tile 1x2",  1, 2, 1),
    "63864": PartSpec("63864", "Tile 1x3",  1, 3, 1),
    "2431":  PartSpec("2431",  "Tile 1x4",  1, 4, 1),
    "3068b": PartSpec("3068b", "Tile 2x2",  2, 2, 1),
    # --- slopes (45°, 1 stud wide unless noted) ---
    "3040b": PartSpec("3040b", "Slope 45° 1x2", 1, 2, 3),
    "3039":  PartSpec("3039",  "Slope 45° 2x2", 2, 2, 3),
    "3037":  PartSpec("3037",  "Slope 45° 2x4", 2, 4, 3),
    # --- round / misc ---
    "4073":  PartSpec("4073",  "Round Plate 1x1", 1, 1, 1),
    "4032":  PartSpec("4032",  "Round Plate 2x2", 2, 2, 1),
    "3062b": PartSpec("3062b", "Round Brick 1x1", 1, 1, 3),
}


# LDraw color codes for the most common LEGO colors. Full list at
# /usr/share/ldraw/LDConfig.ldr or https://ldraw.org/article/547.html.
COLORS: dict[str, int] = {
    "black":            0,
    "blue":             1,
    "green":            2,
    "dark_turquoise":   3,
    "red":              4,
    "dark_pink":        5,
    "brown":            6,    # legacy "brown" — modern is "reddish_brown"
    "light_grey":       7,    # legacy
    "dark_grey":        8,    # legacy
    "light_blue":       9,
    "bright_green":    10,
    "light_turquoise": 11,
    "salmon":          12,
    "pink":            13,
    "yellow":          14,
    "white":           15,
    "light_green":     17,
    "light_yellow":    18,
    "tan":             19,
    "purple":          22,
    "magenta":         26,
    "lime":            27,
    "orange":          25,
    "dark_red":        320,
    "reddish_brown":   70,
    "light_bluish_grey": 71,
    "dark_bluish_grey":  72,
    "medium_blue":     73,
    "medium_green":    74,
    "dark_green":      28,
    # Transparent
    "trans_clear":     47,
    "trans_red":       36,
    "trans_blue":      33,
    "trans_yellow":    46,
    "trans_green":     34,
    "trans_orange":    57,
    "trans_black":     40,
}


def color(name: str) -> int:
    """Look up an LDraw color code by name, raising clearly if missing."""
    try:
        return COLORS[name]
    except KeyError as e:
        raise KeyError(
            f"Unknown color {name!r}. Known: {sorted(COLORS)}"
        ) from e


def part(part_id: str) -> PartSpec:
    try:
        return PARTS[part_id]
    except KeyError as e:
        raise KeyError(
            f"Part {part_id!r} not in catalog. Either add it to PARTS or use "
            f"Model.add(Part(part_id, ...)) to place it directly by id."
        ) from e
