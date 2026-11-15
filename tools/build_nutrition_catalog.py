"""Build a compact, reproducible offline subset from USDA FDC Foundation Foods JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

SOURCE_URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-10-29.zip"
ATTRIBUTION = "U.S. Department of Agriculture, Agricultural Research Service. FoodData Central, 2019. fdc.nal.usda.gov. Foundation Foods release 2026-10. Public domain, CC0 1.0."
NEEDED = {
    "Energy": ("energy_kcal", "KCAL"),
    "Protein": ("protein_g", "G"),
    "Carbohydrate, by difference": ("carbohydrate_g", "G"),
    "Total lipid (fat)": ("fat_g", "G"),
    "Water": ("water_g", "G"),
}


def build(archive: Path, destination: Path) -> dict:
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as zipped:
        candidates = [n for n in zipped.namelist() if n.lower().endswith(".json")]
        if len(candidates) != 1:
            raise ValueError("Expected exactly one USDA FDC JSON in the archive")
        raw = zipped.read(candidates[0])
    parsed = json.loads(raw)
    rows = []
    missing_counts = {key: 0 for key in NEEDED}
    for food in parsed.get("FoundationFoods", []):
        nutrients = {}
        for item in food.get("foodNutrients", []):
            nutrient = item.get("nutrient", {})
            name = nutrient.get("name")
            if name in NEEDED and item.get("amount") is not None:
                field, unit = NEEDED[name]
                actual_unit = (nutrient.get("unitName") or "").upper()
                if (unit == "KCAL" and actual_unit in {"KCAL", "KILOCALORIES"}) or (unit == "G" and actual_unit == "G"):
                    nutrients[field] = item["amount"]
        # Store missing values explicitly as null; never infer zero from absent nutrient rows.
        for name, (field, _) in NEEDED.items():
            if field not in nutrients:
                nutrients[field] = None
                missing_counts[name] += 1
        rows.append({
            "fdc_id": food["fdcId"],
            "description": food["description"],
            "data_type": food.get("dataType", "Foundation"),
            "publication_date": food.get("publicationDate", "2026-10"),
            "portion_records_available": bool(food.get("foodPortions")),
            "per_100g": nutrients,
        })
    rows.sort(key=lambda row: (row["description"].casefold(), row["fdc_id"]))
    document = {
        "schema_version": "1.0.0",
        "catalog_id": "USDA_FDC_FOUNDATION_FOODS_2026_10_ASTHRAL_COMPACT",
        "source_url": SOURCE_URL,
        "source_archive_sha256": archive_hash,
        "source_json_sha256": hashlib.sha256(raw).hexdigest(),
        "generated_at_utc_date": "2026-10-29",
        "attribution": ATTRIBUTION,
        "data_basis": "USDA Foundation Foods measured/reported composition per 100 g edible portion where available; not mission food equivalence.",
        "missing_values": "null means not supplied for this food; null is not zero.",
        "foods": rows,
        "audit": {"food_count": len(rows), "missing_nutrient_counts": missing_counts},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
    destination.write_text(serialized, encoding="utf-8", newline="\n")
    content_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    destination.with_suffix(destination.suffix + ".sha256").write_text(content_hash + "\n", encoding="ascii", newline="\n")
    return document


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path, help="Official USDA FoodData Central Foundation Foods JSON ZIP")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    result = build(args.archive, args.destination)
    print(json.dumps({"catalog": str(args.destination), **result["audit"], "source_archive_sha256": result["source_archive_sha256"], "catalog_content_sha256": hashlib.sha256(args.destination.read_bytes()).hexdigest()}, indent=2))
