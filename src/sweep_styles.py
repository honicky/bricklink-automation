"""Style sweep: render the same view of the same model with different render
styles, so we can eyeball which settings the vision model finds easiest."""

from __future__ import annotations

import sys
import time
from dataclasses import replace
from pathlib import Path

# Local import; treat src as importable.
sys.path.insert(0, str(Path(__file__).parent))
from render import Camera, RenderStyle, render_one  # noqa: E402

# Same camera every time so we're isolating style, not angle.
HERO = Camera("hero", lat=30, lon=45)

VARIANTS: dict[str, RenderStyle] = {
    "01_default":       RenderStyle(),
    "02_no_logos":      RenderStyle(stud_logos=False),
    "03_no_seams":      RenderStyle(seams=False),
    "04_clean":         RenderStyle(stud_logos=False, seams=False),
    "05_black_bg":      RenderStyle(background="0xFF000000"),
    "06_grey_bg":       RenderStyle(background="0xFFC0C0C0"),
    "07_transparent":   RenderStyle(save_alpha=True),
    "08_lowres_512":    RenderStyle(width=512, height=512),
    "09_highres_2048":  RenderStyle(width=2048, height=2048),
    "10_telephoto":     RenderStyle(fov=5.0),
    "11_wide":          RenderStyle(fov=60.0),
    "12_light_overhead": RenderStyle(light_vector="0,1,0.3"),  # mostly-overhead light
    "13_light_camera":  RenderStyle(light_vector="0.5,0.5,1"), # roughly camera-aligned
}


def main(model: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{'variant':<22} {'time_s':>8} {'kb':>8}")
    for name, style in VARIANTS.items():
        t0 = time.time()
        path = render_one(model, out_dir, HERO, style, name_prefix=f"{name}_")
        dt = time.time() - t0
        kb = path.stat().st_size / 1024
        print(f"{name:<22} {dt:>8.2f} {kb:>8.1f}")


if __name__ == "__main__":
    model = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("samples/car.ldr")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("out/sweep_car")
    main(model, out)
