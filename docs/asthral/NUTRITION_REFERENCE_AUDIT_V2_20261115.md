# USDA energy-reference audit and versioned migration

The official Foundation Foods ZIP contains several separately named energy references. The v1 compact extractor read the nutrient named Energy (1008, kcal) only. Its statement that 329 foods lacked energy described that one field, not every published energy reference. V2 corrects representation without selecting a preferred calculation method, computing a new value from macros, or changing the original medical engine.

Official source: https://fdc.nal.usda.gov/download-datasets/ ; dataset https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-10-29.zip . USDA public-domain/CC0 reuse attribution is preserved. This is food composition, not a mission-food or clinical nutrition protocol.

| Source inventory | Foods |
|---|---:|
| Total Foundation Foods | 424 |
| Energy 1008, kcal | 95 |
| Energy, Atwater General Factors 2047, kcal | 279 |
| Energy, Atwater Specific Factors 2048, kcal | 200 |
| No value for any of these three references | 50 |

Counts overlap. 329 still lack the original 1008 field. Protein is absent for 17, carbohydrate 50, fat 31 and water 8. These nulls remain unknown. The kJ energy nutrient is not relabelled kcal.

Source archive SHA-256: `dd414cc9f1a132626bad354ef6655972c78b44aff14f16114dc899708663c579`. The builder now refuses any other archive before generating output. V2 content SHA-256: `266442107d4a7817acf76497df9f7927f54b43f5e0fd9c009e6cf5cc41ecf346`. V1 bytes are preserved in foods-v1.json, SHA-256 `a09e222154963247cbb4f24b0a643385a6f2c5fac26d4aa0956dab34d1d6ad17`.

V2 adds named energy references and per-method availability counts; original per_100g fields are unchanged. Default logging uses v2 plus the legacy 1008 energy method. Selecting another method is explicit and recorded. Consumers can explicitly request v1. Existing stored records retain their historical catalog and values; there is no silent migration or retrospective reinterpretation. See web-local/INTEGRATION_CONTRACTS.md for exact fields.

Regression example from the original ZIP: FDC 2262074, Almond butter, creamy, has 645 kcal/100 g General and 603 kcal/100 g Specific, with no 1008 value. For a software-test 10 g portion the respective estimates are 64.5 and 60.3 kcal; default 1008 remains null. This is a provenance/scaling regression, not dietary advice. Tests also preserve a v1 85 kcal reference, reject malformed selectors and unpinned source bytes, and retain incomplete daily totals. The source archive can be regenerated with `python tools/build_nutrition_catalog.py <official-zip> web-local/src/nutrition/foods.json`.

Not implemented: nutrition adequacy, mission-food equivalence, personalized intake targets, corrections/supersession UI and additional USDA categories. No missing value is filled automatically. Method differences, portion uncertainty and unlogged foods prevent an intake/energy-balance claim.
