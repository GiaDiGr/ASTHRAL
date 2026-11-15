# ASTHRAL curated space-health source summary

Version: 2026-11-15. Authoring status: project summary, not a clinical guideline. The full source documents remain at their publishers' URLs; only bibliographic metadata and the summaries below are distributed. Every subject-level decision remains outside this document.

## Space-weather event data — SRC-CCMC-DONKI-2026

CCMC DONKI is a public event and modeling database. Its records can include event observations, analyses, model results, linked events and notifications. The service describes its data as intended for research and prototyping and disclaims warranties. A flare, CME or SEP record is an environmental event report; it is not a measurement of a crew member's exposure and does not imply an individual's dose, location-specific hazard, clinical diagnosis or operational warning. ASTHRAL preserves event identifiers and timestamps, labels live versus historical fixture data, and never lets an event alter clinical records.

## HRP evidence catalogue — SRC-NASA-HRR-2026

NASA's Human Research Roadmap groups evidence reports by spaceflight health risk, including sleep and circadian health, reduced fitness, bone fracture, nutrition, behavioral health and medical autonomy. Catalogue presence indicates that a topic has been researched; it does not mean that a particular intervention is established or applicable to every mission. The catalogue links to reports with different publication dates and evidence maturity. Reviewers should inspect the current official catalogue and full report before making a clinical or program decision.

## Sleep, circadian timing and workload — SRC-NASA-HRR-SLEEP-2016

The 2016 HRP sleep evidence report reviews risk questions and research on sleep loss, circadian desynchronization, workload, performance and health outcomes in spaceflight contexts. It describes measurement and evidence limitations; it is not a universal sleep-duration prescription. ASTHRAL's sleep entry is a voluntary self-reported duration and optional subjective rating, not a validated sleep sensor, screening result, or inference of impairment.

## Exercise, fitness and musculoskeletal health — SRC-NASA-HRR-FITNESS-2024; SRC-NASA-HRR-BONE-2024

The HRP fitness and bone evidence reports address reduced cardiorespiratory and musculoskeletal fitness and fracture risk associated with spaceflight-related bone changes. These reports provide research context, not a user-specific exercise or rehabilitation plan. ASTHRAL provides project-authored generic movement examples to support a manual software workflow; they are not NASA training protocol content, approved mission countermeasures, or individualized prescriptions. The user records activity, workload, sets, repetitions and time. The app does not estimate VO2, strength, bone density, injury risk, form or readiness.

## Nutrition — SRC-NASA-HRR-NUTRITION-2020

NASA's 2020 nutrition evidence report reviews nutrition research questions and human adaptation in spaceflight. ASTHRAL's offline food-composition estimates use a 424-food subset of USDA FoodData Central Foundation Foods release 2026-10, scaled from the source's per-100-g entries by a user-entered mass. These estimates may not match mission foods, packaging, preparation, or consumed amounts. Source nulls remain missing, not zero. A food-composition estimate does not establish an astronaut's intake, energy balance, hydration status, or nutrient adequacy. ASTHRAL offers no nutritional target, supplement advice, or clinical interpretation.

## Standards and applicability — SRC-NASA-STD3001-V1-REVC; SRC-NASA-STD3001-V2-REVD; SRC-NASA-STD3001-V2-REVF

NASA-STD-3001 includes crew-health and human-factors/environmental-health requirements. At the 2026-11-15 review date, the NASA standards catalogue identifies Volume 2 Revision F (document date 2026-07-14) as active; the registry's Revision D entry is historical. Program documents and tailoring govern applicability; copying a number or sentence from a standard into a general-purpose application would not establish an applicable operational requirement. ASTHRAL does not implement dose limits or suitability thresholds and does not issue a standards-compliance verdict.

## Radiation observations and dosimeter context — SRC-NASA-SRAG-CAD-2026; SRC-NASA-NESC-RP-20-01589

NASA SRAG describes the Crew Active Dosimeter as a time-resolved personal absorbed-dose instrument. NASA's NESC report discusses HERA and CAD in a particular Orion configuration; hardware and measurement availability depend on vehicle and mission design. ASTHRAL has no verified hardware adapter. Manual records are explicitly unverified. Synthetic and modelled values are distinguished from measured observations.

Absorbed dose (Gy) and dose-equivalent/effective-dose quantities (Sv) are different physical quantities. The app converts units only within a declared quantity family. It does not convert Gy to Sv, estimate organ doses, apply radiation quality factors, reconstruct shielding, or interpret exposure as safe/unsafe. The optional dose-rate integral uses a trapezoidal linear-between-samples assumption only across compatible, valid, measured adjacent records from one instrument, segment and location; gaps remain explicit and no values are imputed.

## API transport — SRC-NASA-CCMC-API-2026

The CCMC API documentation describes the public DONKI service and its response schemas. ASTHRAL sends bounded date-only requests to the official host, omits cookies/credentials and never includes a profile identifier or health record. API success only confirms transport and parsability; retrieved event metadata retain source attribution and do not become biomedical evidence or clinical rules.

## Source registry

See `sources.json` for stable IDs, URLs, publication/version information, evidence category, claim mapping, review date and redistribution status. See `source-integrity.json` for local SHA-256 values. Hashes protect the recorded bytes from unnoticed edits; they do not verify scientific accuracy, source currency or clinical validity.
