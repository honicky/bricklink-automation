"""LDraw model state + serialization.

The whole library is one file. Coordinates: LDraw native conventions —
the X/Z plane is horizontal, Y points DOWN (gravity is +Y), 1 stud =
20 LDU horizontal, 1 brick height = 24 LDU = 3 plate heights = 24 LDU.

For convenience there's a stud-coordinate helper `place(...)` that takes
(stud_x, stud_z, level_in_plates) with the build plate at level=0 and
positive levels going UP, plus an integer 0/1/2/3 for quarter-turn yaw.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field, replace
from pathlib import Path

# --- coord constants ----------------------------------------------------------

STUD_LDU = 20      # 1 stud horizontal = 20 LDU
BRICK_LDU = 24     # 1 brick height = 24 LDU
PLATE_LDU = 8      # 1 plate height = 8 LDU = 1/3 brick
# So: a brick sitting on the build plate spans Y = 0 (top of plate) down to
# Y = -BRICK_LDU. A part's local origin is at the centre of its bottom face.

# Identity and quarter-turn rotation matrices around vertical (Y) axis, in
# row-major 9-tuple form as LDraw's "1" lines expect.
_ROT = {
    0: (1, 0, 0,  0, 1, 0,  0, 0, 1),    # 0°
    1: (0, 0, 1,  0, 1, 0, -1, 0, 0),    # 90° CCW about Y (when looking down +Y, i.e. looking up)
    2: (-1, 0, 0, 0, 1, 0,  0, 0, -1),   # 180°
    3: (0, 0, -1, 0, 1, 0,  1, 0, 0),    # 270°
}


# --- types --------------------------------------------------------------------


@dataclass(frozen=True)
class Part:
    """One placed part: an LDraw "1" line.

    `position` and `rotation` are in LDraw native coords. Use `Model.place(...)`
    if you'd rather think in studs and quarter turns.
    """
    part_id: str                          # e.g. "3001" for 2x4 brick
    color: int                            # LDraw color code, e.g. 4 = red
    position: tuple[float, float, float]  # (x, y, z) LDU; remember Y is DOWN
    rotation: tuple[float, ...] = _ROT[0] # 9-element row-major matrix

    def to_ldraw_line(self) -> str:
        x, y, z = self.position
        m = " ".join(_fmt(v) for v in self.rotation)
        return f"1 {self.color} {_fmt(x)} {_fmt(y)} {_fmt(z)} {m} {self.part_id}.dat"


def _fmt(v: float) -> str:
    """LDraw-style number formatting: ints stay ints, floats stay short."""
    if isinstance(v, int) or v == int(v):
        return str(int(v))
    return f"{v:g}"


@dataclass
class Model:
    name: str = "model"
    author: str = "bricklink-automation"
    parts: list[Part] = field(default_factory=list)

    # --- placement ------------------------------------------------------------

    def add(self, part: Part) -> Part:
        self.parts.append(part)
        return part

    def remove(self, part: Part) -> None:
        # Remove first match by identity-ish equality.
        self.parts.remove(part)

    def place(
        self,
        part_id: str,
        color: int,
        stud_x: float = 0,
        stud_z: float = 0,
        level: int = 0,
        rotate: int = 0,
    ) -> Part:
        """Place a part on a stud-grid.

        - stud_x, stud_z: horizontal position in studs (centred on the part).
        - level: vertical position in PLATE units, with 0 = sitting on the
          build plate. Stack a brick on top of another brick at level=3.
        - rotate: 0/1/2/3 quarter-turns yaw about vertical axis.
        """
        position = (stud_x * STUD_LDU, -level * PLATE_LDU, stud_z * STUD_LDU)
        return self.add(Part(part_id, color, position, _ROT[rotate % 4]))

    # --- serialization --------------------------------------------------------

    def to_ldr(self) -> str:
        lines = [
            f"0 {self.name}",
            f"0 Name: {self.name}.ldr",
            f"0 Author: {self.author}",
            "",
        ]
        lines.extend(p.to_ldraw_line() for p in self.parts)
        lines.append("")  # trailing newline
        return "\n".join(lines)

    def write_ldr(self, path: Path | str) -> Path:
        path = Path(path)
        path.write_text(self.to_ldr(), encoding="utf-8")
        return path

    def write_io(self, path: Path | str) -> Path:
        """Write Studio's .io file. .io is a zip with model.ldr inside.

        Studio also stores its own metadata (camera, groups, BOM hints) in
        a model.ini, but Studio happily opens an .io that contains only
        model.ldr — it'll fill in defaults.
        """
        path = Path(path)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("model.ldr", self.to_ldr())
        return path

    # --- conveniences ---------------------------------------------------------

    def __len__(self) -> int:
        return len(self.parts)

    def copy(self) -> "Model":
        return replace(self, parts=list(self.parts))
