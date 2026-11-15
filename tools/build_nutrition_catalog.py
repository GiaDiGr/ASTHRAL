"""Build a compact, reproducible offline subset from USDA FDC Foundation Foods JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

SOURCE_URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-10-29.zip"
SOURCE_SHA256 = "dd414cc9f1a132626bad354ef6655972c78b44aff14f16114dc899708663c579"
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
    if archive_hash != SOURCE_SHA256:
        raise ValueError("USDA_SOURCE_ARCHIVE_HASH_MISMATCH")
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
        energy_references = {"DECLARED_1008": None, "ATWATER_GENERAL_2047": None, "ATWATER_SPECIFIC_2048": None}
        for item in food.get("foodNutrients", []):
            nutrient = item.get("nutrient", {})
            name = nutrient.get("name")
            energy_key = {1008: "DECLARED_1008", 2047: "ATWATER_GENERAL_2047", 2048: "ATWATER_SPECIFIC_2048"}.get(nutrient.get("id"))
            if energy_key and (nutrient.get("unitName") or "").upper() == "KCAL" and item.get("amount") is not None:
                energy_references[energy_key] = item["amount"]
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
            "energy_references_kcal_per_100g": energy_references,
        })
    rows.sort(key=lambda row: (row["description"].casefold(), row["fdc_id"]))
    document = {
        "schema_version": "2.0.0",
        "catalog_id": "USDA_FDC_FOUNDATION_FOODS_2026_10_ASTHRAL_COMPACT_V2",
        "source_url": SOURCE_URL,
        "source_archive_sha256": archive_hash,
        "source_json_sha256": hashlib.sha256(raw).hexdigest(),
        "generated_at_utc_date": "2026-10-29",
        "attribution": ATTRIBUTION,
        "data_basis": "USDA reported reference composition per 100 g edible portion, with explicitly named energy calculation methods where available; not mission food equivalence.",
        "missing_values": "null means not supplied for this specific nutrient/method; alternative energy methods may exist. Null is not zero.",
        "energy_methods": {"DECLARED_1008": "Energy (USDA nutrient 1008)", "ATWATER_GENERAL_2047": "Energy (Atwater General Factors), USDA nutrient 2047", "ATWATER_SPECIFIC_2048": "Energy (Atwater Specific Factors), USDA nutrient 2048"},
        "foods": rows,
        "audit": {"food_count": len(rows), "missing_nutrient_counts": missing_counts,
            "energy_method_available_counts": {key: sum(row["energy_references_kcal_per_100g"][key] is not None for row in rows) for key in ("DECLARED_1008", "ATWATER_GENERAL_2047", "ATWATER_SPECIFIC_2048")},
            "foods_without_any_energy_reference": sum(all(value is None for value in row["energy_references_kcal_per_100g"].values()) for row in rows)},
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
