"""Create or verify SHA-256 metadata for the small, locally authored science registry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/asthral/science/SPACE_HEALTH_EVIDENCE.md",
         "docs/asthral/science/space-health-summary.md",
         "docs/asthral/science/sources.json")
OUT = ROOT / "docs/asthral/science/source-integrity.json"


def manifest() -> dict:
    rows = []
    for relative in FILES:
        path = ROOT / relative
        raw = path.read_bytes()
        rows.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return {"schema_version": "1.0.0", "algorithm": "SHA-256", "files": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = json.dumps(manifest(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != expected:
            print("SOURCE_INTEGRITY_MISMATCH")
            return 1
        print("SOURCE_INTEGRITY_OK")
        return 0
    OUT.write_text(expected, encoding="utf-8", newline="\n")
    print(OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
