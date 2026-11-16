"""Generate reproducible blue-to-violet wave palettes for the local starfields."""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = ROOT / "web-local" / "src" / "cosmic-scenes"
SCENE_COUNT = 24
WAVE_PERIOD_TABS = 10
GRADIENT_ENDPOINTS = {
    "a": ((27, 110, 167), (119, 49, 164)),
    "b": ((31, 105, 165), (100, 48, 165)),
}


def wave_position(scene_index: int) -> float:
    """Return 0 for blue and 1 for violet, completing one wave every 10 tabs."""
    phase = (scene_index % WAVE_PERIOD_TABS) / WAVE_PERIOD_TABS
    return (1 - math.cos(2 * math.pi * phase)) / 2


def blend(start: tuple[int, int, int], end: tuple[int, int, int], amount: float) -> str:
    channels = tuple(round(left + (right - left) * amount) for left, right in zip(start, end))
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def palette_for_scene(scene_index: int) -> dict[str, str]:
    position = wave_position(scene_index)
    return {
        gradient: blend(start, end, position)
        for gradient, (start, end) in GRADIENT_ENDPOINTS.items()
    }


def replace_palette(svg: str, palette: dict[str, str], path: Path) -> str:
    result = svg
    for gradient, color in palette.items():
        pattern = re.compile(
            rf'(<radialGradient id="{gradient}"><stop stop-color=")#[0-9a-fA-F]{{6}}(")'
        )
        result, count = pattern.subn(rf"\g<1>{color}\g<2>", result)
        if count != 1:
            raise ValueError(f"Expected one first stop in gradient {gradient!r}: {path}")
    return result


def generate(*, check: bool = False) -> list[Path]:
    changed: list[Path] = []
    for scene_index in range(SCENE_COUNT):
        path = SCENES / f"scene-{scene_index:02}.svg"
        if not path.is_file():
            raise FileNotFoundError(path)
        before = path.read_text(encoding="utf-8")
        after = replace_palette(before, palette_for_scene(scene_index), path)
        if before != after:
            if check:
                changed.append(path)
            else:
                path.write_text(after, encoding="utf-8", newline="")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if any palette needs regeneration")
    args = parser.parse_args()
    changed = generate(check=args.check)
    if changed:
        print("Palette regeneration required for: " + ", ".join(path.name for path in changed))
        return 1
    action = "verified" if args.check else "generated"
    print(f"{action.title()} {SCENE_COUNT} starfield palettes; wave period: {WAVE_PERIOD_TABS} tabs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
