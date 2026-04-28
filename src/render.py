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
    """Knobs we want to sweep for the vision-quality study."""
    width: int = 1024
    height: int = 1024
    edges: bool = True               # draw black edge lines
    conditional_edges: bool = True   # smooth edges on curved parts
    quality_lines: int = 3           # 0..3, higher = better antialiased edges
    background: str = "0xFFFFFF"     # hex 0xRRGGBB; e.g. 0xFFFFFF white, 0x808080 grey
    save_alpha: bool = False         # transparent bg PNG
    show_studs: bool = True          # LEGO logos on studs
    seams: bool = True               # part-to-part seam lines
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
        f"-BackgroundColor={style.background}",
        f"-FOV={style.fov}",
        f"-LightVector={style.light_vector}",
        f"-ShowEdges={int(style.edges)}",
        f"-ConditionalLines={int(style.conditional_edges)}",
        f"-QualityLines={style.quality_lines}",
        f"-DrawConditionalHighlights={int(style.conditional_edges)}",
        f"-ShowStuds={int(style.show_studs)}",
        f"-Seams={int(style.seams)}",
        f"-SaveAlpha={int(style.save_alpha)}",
        # Quality flags worth always-on for spike work:
        "-AutoCrop=0",
        "-SaveActualSize=0",
        "-Subsample=1",         # 2x supersampling for AA
    ]
    args.extend(style.extra)
    return args


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
    p.add_argument("--background", default="0xFFFFFF")
    p.add_argument("--no-edges", action="store_true")
    p.add_argument("--no-studs", action="store_true")
    p.add_argument("--alpha", action="store_true", help="Transparent background PNG")
    p.add_argument("--prefix", default="", help="Filename prefix for outputs")
    p.add_argument("--cameras", help="Comma-separated camera names (default: all)")
    args = p.parse_args(argv)

    style = RenderStyle(
        width=args.width,
        height=args.height,
        background=args.background,
        edges=not args.no_edges,
        show_studs=not args.no_studs,
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
