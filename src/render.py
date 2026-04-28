"""LDView-based renderer for LDraw models.

Spike-quality. Wraps the `ldview` CLI to produce one or more camera-angle PNGs
for a given `.ldr`/`.dat`/`.mpd` file. Mesa software-fallback env vars are set
so this works on headless boxes without a GPU or `/dev/dri`.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

LDVIEW_BIN = shutil.which("ldview") or "/usr/bin/ldview"

# Mesa knobs: force the software rasterizer + EGL surfaceless so OSMesa LDView
# works on headless VMs without /dev/dri. Harmless on a normal desktop.
SOFTWARE_GL_ENV = {
    "LIBGL_ALWAYS_SOFTWARE": "1",
    "EGL_PLATFORM": "surfaceless",
    "MESA_LOADER_DRIVER_OVERRIDE": "swrast",
}


@dataclass(frozen=True)
class Camera:
    name: str
    lat: float  # latitude degrees, 0 = equator, 90 = top-down
    lon: float  # longitude degrees
    ortho: bool = False  # orthographic vs perspective


# Default 6-view set: 4 sides + top + a 3/4 hero shot.
DEFAULT_CAMERAS: tuple[Camera, ...] = (
    Camera("hero", lat=30, lon=45),
    Camera("front", lat=0, lon=0),
    Camera("right", lat=0, lon=90),
    Camera("back", lat=0, lon=180),
    Camera("left", lat=0, lon=270),
    Camera("top", lat=89.9, lon=0),
)


@dataclass
class RenderStyle:
    """Knobs we want to sweep for the vision-quality study.

    Note: many plausible-sounding LDView CLI flags (EdgeLines, EdgesOnly,
    HideStuds, ConditionalEdges, Antialias, ...) are silently ignored by
    the OSMesa build — see VERIFIED_FLAGS at the bottom of this file for
    the (small) set that actually takes effect. The fields below correspond
    to flags that have been verified to change pixels.
    """
    width: int = 1024
    height: int = 1024
    background: str = "0xFFFFFFFF"   # AARRGGBB uint32; 0xFFFFFFFF white opaque
    save_alpha: bool = False         # transparent PNG (overrides background)
    stud_logos: bool = True          # LEGO logo texture on studs
    seams: bool = True               # part-to-part gap lines
    fov: float = 30.0                # perspective FOV in degrees
    # LDView's default LightVector lights only some camera angles well — at
    # lat=0 the front face goes pure-ambient and dark colors desaturate (black
    # renders as grey). LightVector=1,1,1 puts the light upper-front-right in
    # world space, which keeps colors saturated and black=black across all
    # six default cameras while still giving the hero shot good depth shading.
    light_vector: str = "1,1,1"
    extra: tuple[str, ...] = field(default_factory=tuple)  # raw passthrough flags


def _ldview_args(model: Path, snapshot: Path, cam: Camera, style: RenderStyle) -> list[str]:
    args: list[str] = [
        LDVIEW_BIN,
        str(model),
        f"-SaveSnapshot={snapshot}",
        f"-SaveWidth={style.width}",
        f"-SaveHeight={style.height}",
        f"-DefaultLatLong={cam.lat},{cam.lon}",
        f"-BackgroundColor3={style.background}",
        f"-FOV={style.fov}",
        f"-LightVector={style.light_vector}",
        f"-TextureStuds={int(style.stud_logos)}",
        f"-Seams={int(style.seams)}",
        f"-SaveAlpha={int(style.save_alpha)}",
    ]
    args.extend(style.extra)
    return args


# Flags verified to change rendered output in LDView 4.7 OSMesa on Linux.
# Anything else (EdgeLines, EdgesOnly, HideStuds, ConditionalEdges,
# Antialias, AutoCrop, LineSmoothing, ...) is silently ignored from the CLI.
VERIFIED_FLAGS = (
    "SaveSnapshot", "SaveWidth", "SaveHeight",
    "DefaultLatLong", "FOV",
    "BackgroundColor3", "SaveAlpha",
    "LightVector",
    "TextureStuds", "Seams",
)


def render_one(
    model: Path,
    out_dir: Path,
    cam: Camera,
    style: RenderStyle | None = None,
    *,
    name_prefix: str = "",
) -> Path:
    style = style or RenderStyle()
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot = out_dir / f"{name_prefix}{cam.name}.png"
    cmd = _ldview_args(model, snapshot, cam, style)

    env = {**os.environ, **SOFTWARE_GL_ENV}
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if not snapshot.exists():
        raise RuntimeError(
            f"LDView did not produce {snapshot}.\n"
            f"cmd: {' '.join(cmd)}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return snapshot


def render_views(
    model: Path,
    out_dir: Path,
    cameras: tuple[Camera, ...] = DEFAULT_CAMERAS,
    style: RenderStyle | None = None,
    *,
    name_prefix: str = "",
) -> list[Path]:
    return [render_one(model, out_dir, c, style, name_prefix=name_prefix) for c in cameras]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render LDraw model to PNGs from multiple angles.")
    p.add_argument("model", type=Path, help="Path to .ldr / .dat / .mpd file")
    p.add_argument("-o", "--out", type=Path, default=Path("out"), help="Output dir")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--background", default="0xFFFFFFFF",
                   help="AARRGGBB uint32, e.g. 0xFFFFFFFF white, 0xFF000000 black")
    p.add_argument("--no-logos", action="store_true", help="Disable LEGO logo on studs")
    p.add_argument("--no-seams", action="store_true", help="Disable part-to-part gap lines")
    p.add_argument("--alpha", action="store_true", help="Transparent background PNG")
    p.add_argument("--prefix", default="", help="Filename prefix for outputs")
    p.add_argument("--cameras", help="Comma-separated camera names (default: all)")
    args = p.parse_args(argv)

    style = RenderStyle(
        width=args.width,
        height=args.height,
        background=args.background,
        stud_logos=not args.no_logos,
        seams=not args.no_seams,
        save_alpha=args.alpha,
    )
    cams = DEFAULT_CAMERAS
    if args.cameras:
        wanted = {n.strip() for n in args.cameras.split(",")}
        cams = tuple(c for c in DEFAULT_CAMERAS if c.name in wanted)
        if not cams:
            print(f"No cameras matched {wanted!r}", file=sys.stderr)
            return 2

    paths = render_views(args.model, args.out, cams, style, name_prefix=args.prefix)
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
