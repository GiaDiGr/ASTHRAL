# ASTHRAL space-health evidence notes

Review date: 2026-11-15. These are concise, project-authored summaries of authoritative source pages. The linked source documents are not republished in the application. They are context for education and retrieval, not new clinical criteria or individualized plans.

## What the source audit found

The previous browser vector index bundled six chunks from an ASTHRAL-authored implementation note, even though the build-time sparse corpus held more project, research-synthesis and short-excerpt files. The integration build now bundles eight hash-addressed source documents and 586 sparse retrieval blocks, including this authored summary. The optional MiniLM vector index remains the earlier six chunks; it is lexical-candidate-gated and is not a comprehensive scientific index. This is still not a broad full-text space-medicine library. NASA's Human Research Roadmap lists separate reports for sleep/circadian/workload, bone fracture, reduced cardiorespiratory and musculoskeletal fitness, nutrition, SANS, medical autonomy and behavioral health. ASTHRAL includes links and short authored summaries only for the newly curated topics. Full-text redistribution and licensing of third-party material have not been cleared.

The corpus intentionally distinguishes NASA standards, NASA research evidence reports, operational instrumentation descriptions, NASA technical reports, project-authored summaries, and clinical decision rules. Only the pre-existing clinical rule package can emit diagnostic results. Space-weather events, self-reported prevention entries, radiation readings, and the new summaries cannot modify it.

## Curated source notes

### NASA DONKI

The CCMC DONKI system records event reports, analyses, models, event linkages and notifications. CCMC says the records are shared for space-weather research and prototyping, with a no-warranty disclaimer. ASTHRAL displays the event's stated UTC time, identifier, selected reported parameters and official event link. It does not derive individual exposure or a universal danger score from an event.

### Human Research Program evidence

NASA's Human Research Roadmap catalogue organizes risk evidence reports. The sleep report describes spaceflight observations and research gaps around sleep, circadian desynchronization, workload, measurement and individual variability. The current UI records duration and a voluntary subjective rating only; it does not set a target, infer sleep debt, or diagnose impairment.

NASA's aerobic and muscle evidence report and bone-fracture report provide research context on fitness and skeletal risk. ASTHRAL records user-entered exercise-session details only; it does not generate NASA-approved training plans, measure strength from a phone, infer bone loss, or personalize rehabilitation.

NASA nutrition evidence reports document spaceflight research questions and measured diet information. ASTHRAL records a user note and optionally a user-entered fluid volume. It does not invent food composition, energy values, nutrient adequacy, hydration targets, or supplement advice.

### NASA human-spaceflight standards and radiation monitoring

NASA-STD-3001 Volume 1 is the crew-health standard; Volume 2 covers human factors, habitability and environmental health. As of this review date, NASA's standards catalogue lists Volume 2 Revision F (document date 2026-07-14) as active; Revision D remains a historical registry entry. Programs tailor applicability to mission profile and procurement strategy. The sources describe individual and area radiation monitoring for different exposure classes and contexts.

NASA SRAG describes Crew Active Dosimeters (CAD) as personal, time-resolved absorbed-dose monitoring equipment. NASA's Artemis hardware descriptions distinguish personal crew dosimetry from area-monitoring hardware such as HERA and state that instrument deployment and EVA capability depend on the mission/hardware configuration. ASTHRAL has no CAD, HERA, passive dosimeter, EVA suit, Bluetooth or USB adapter. Every record entered here remains marked “sensor verified by ASTHRAL: no.”

Absorbed dose (Gy) and dose equivalent/effective dose (Sv) remain separate quantities. Conversion factors, organ-dose reconstruction, radiation quality/RBE, shielding transport and risk models are outside this implementation. Optional trapezoidal integration applies only to compatible valid readings from one declared instrument, mission segment and location, with an explicit user-selected maximum interval; it labels the linear-between-samples assumption and reports gaps. A personal dosimeter reading does not become effective dose through this calculator.

## Source inventory and reuse

Machine-readable citation and review metadata are in `sources.json`. The redistributable content in ASTHRAL is limited to project-authored summaries and bibliographic metadata. Full NASA PDFs, NASA standards, journal papers and third-party contents remain at their official source links. Redistribution permission has not been asserted where not explicitly determined. `source-integrity.json` hashes the local summary and registry; they do not hash or authenticate remote content.

## Evidence limitations

- Web search and retrieval smoke checks are not systematic reviews, evidence grading, or clinical validation.
- Publication metadata and a hash confirm file integrity, not the truth or currency of a claim.
- Some linked NASA evidence reports have older publication dates; users should follow the live HRP catalogue for revisions.
- NASA standards apply through program-specific tailoring and should not be reimplemented from a simplified UI summary.
- No radiation unit in this app is interpreted as safe/unsafe, a permissible-exposure-limit status, health risk, flight eligibility, or need for EVA action.
- No DONKI notification is represented as an authorized personal warning or background push alert.
