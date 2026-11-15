"""Download selected, checksum-pinned research model assets into ignored storage."""
from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "local_ai" / "computer-vision"
ASSETS = {
    "oct": (
        "oct/best_model.pth",
        "https://raw.githubusercontent.com/Strange-Philip/oct-retinal-layer-segmentation/main/checkpoints/best_model.pth",
        "e085d37bc04f716ee3417bbd768fa4aa392a24fb62c0371e066279e6dd7d314a",
    ),
    "motion": (
        "motion/holistic_landmarker.task",
        "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/holistic_landmarker/float16/1/holistic_landmarker.task",
        "e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8",
    ),
}
BLOCKED_ASSETS = {"echo": "EchoNet rights have not been independently established; written permission and checkpoint terms must be reviewed before download or use."}


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def install(name: str) -> Path:
    if name in BLOCKED_ASSETS:
        raise PermissionError(f"{name}: {BLOCKED_ASSETS[name]}")
    relative, url, expected = ASSETS[name]
    destination = ROOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        actual = digest(destination)
        if actual != expected:
            raise RuntimeError(f"Existing {name} asset has an unexpected SHA-256; it was left untouched.")
        print(f"{name}: already installed and checksum verified ({actual})")
        return destination
    handle, temporary = tempfile.mkstemp(prefix="asthral-cv-", suffix=".download", dir=destination.parent)
    os.close(handle)
    temporary_path = Path(temporary)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "ASTHRAL-computer-vision-setup"})
        with urllib.request.urlopen(request, timeout=90) as response, temporary_path.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        actual = digest(temporary_path)
        if actual != expected:
            raise RuntimeError(f"{name} asset SHA-256 mismatch; downloaded file was discarded.")
        temporary_path.replace(destination)
        print(f"{name}: installed at {destination} ({actual})")
        return destination
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=[*ASSETS, *BLOCKED_ASSETS, "all"], help="Explicitly select an asset; blocked assets are refused pending rights review.")
    args = parser.parse_args()
    if args.model in BLOCKED_ASSETS:
        parser.error(f"{args.model}: {BLOCKED_ASSETS[args.model]}")
    names = list(ASSETS) if args.model == "all" else [args.model]
    for name in names:
        install(name)


if __name__ == "__main__":
    main()
