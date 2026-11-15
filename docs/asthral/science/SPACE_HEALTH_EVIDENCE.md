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

NASA nutrition evidence reports document spaceflight research questions and measured diet information. ASTHRAL separately uses USDA FDC Foundation Foods release 2026-10 for general composition estimates on a 424-food offline subset, when nutrient values are available. Portion scaling is based on a user-entered gram amount; estimates are not mission-food matches or measured intake. Missing source values remain null. ASTHRAL does not calculate nutrient adequacy, hydration targets, or supplement advice. See `sources.json` for USDA attribution and reuse metadata.

### EVA thermal-sensing prototypes and evidence boundaries

The T-EVA journal article is an engineering prototype report with upper-body sensor placements and garment/electronics testing; the authors describe additional MDRS and lunar-like testing as future work. It is not flight qualification, a clinical validation study, or a source of medical cutoffs ([Palacios et al., 2023](https://doi.org/10.14569/IJACSA.2023.0140969)). The 2024 IAF contribution describes an embedded spacesuit temperature-sensor network, wrist display, and mission-control link; its UTEC abstract likewise puts analog-environment testing in future work ([Palacios et al., 2024](https://doi.org/10.52202/078359-0051); [UTEC abstract](https://cris.utec.edu.pe/en/publications/biomedical-embedded-system-for-monitoring-temperature-in-spacesui/)). These sources support engineering context only.

One component detail needs engineering follow-up: the T-EVA article describes a DS18B20 as an analog sensor with 10 mV/°C output, whereas the manufacturer datasheet defines the DS18B20 as a digital 1-Wire thermometer. Do not reuse the article's sensor specification until the exact component/probe and calibration method are reconciled ([manufacturer data sheet](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf)). The second paper's institutional and proceedings records also disagree on co-author names/order; the original proceedings title page is needed for a final full-author citation.

NASA Volume 2 Revision F is the active standard in the NASA catalogue as of this review date; OCHMO-TB-050 is a reference brief based on Volume 2 Revision E and does not supersede program requirements. Current controlled requirements and mission tailoring, not an ASTHRAL summary, determine applicability ([NASA standard record](https://standards.nasa.gov/node/237); [OCHMO technical brief](https://www.nasa.gov/wp-content/uploads/2025/09/ochmo-tb-050-spacesuits.pdf)). A NASA simulated-EVA temperature-prediction study used heart rate and metabolic rate and reports development/test datasets of n=6 each; the result is specific to its simulator data and does not establish flight or clinical validation ([NASA NTRS](https://ntrs.nasa.gov/citations/20230016649)).

Barreto et al.'s 2023 micro-review concerns space agriculture and mechatronics for space food production. It should be cited in agriculture/mechatronics discussions only; it is not evidence for EVA biomedical monitoring or thermal criteria ([IEEE DOI](https://doi.org/10.1109/INOCON57975.2023.10101312); [UTEC institutional metadata](https://cris.utec.edu.pe/en/publications/space-agriculture-and-mechatronic-technologies-micro-review-and-m/)).

## Exercise example scope

ASTHRAL's generic exercise examples are project-authored interaction content, not NASA training-protocol content. They do not prescribe frequency, duration, intensity, sets, repetitions, equipment, progression or rehabilitation. Users enter their own activity only; mission restrictions and clinician authorization remain external. Pose tracking is unavailable without a verified local model and runtime.

### NASA human-spaceflight standards and radiation monitoring

NASA-STD-3001 Volume 1 is the crew-health standard; Volume 2 covers human factors, habitability and environmental health. As of this review date, NASA's standards catalogue lists Volume 2 Revision F (document date 2026-07-14) as active; Revision D remains a historical registry entry. Programs tailor applicability to mission profile and procurement strategy. The sources describe individual and area radiation monitoring for different exposure classes and contexts.

NASA SRAG describes Crew Active Dosimeters (CAD) as personal, time-resolved absorbed-dose monitoring equipment. NASA's Artemis hardware descriptions distinguish personal crew dosimetry from area-monitoring hardware such as HERA and state that instrument deployment and EVA capability depend on the mission/hardware configuration. ASTHRAL has no CAD, HERA, passive dosimeter, EVA suit, Bluetooth or USB adapter. Every record entered here remains marked “sensor verified by ASTHRAL: no.”

Absorbed dose (Gy) and dose equivalent/effective dose (Sv) remain separate quantities. Conversion factors, organ-dose reconstruction, radiation quality/RBE, shielding transport and risk models are outside this implementation. Optional trapezoidal integration applies only to compatible valid readings from one declared instrument, mission segment and location, with an explicit user-selected maximum interval; it labels the linear-between-samples assumption and reports gaps. A personal dosimeter reading does not become effective dose through this calculator.

## Source inventory and reuse

Machine-readable citation and review metadata are in `sources.json`. The redistributable content in ASTHRAL is limited to project-authored summaries and bibliographic metadata. Full NASA PDFs, NASA standards, journal papers and third-party contents remain at their official source links. Redistribution permission has not been asserted where not explicitly determined. `source-integrity.json` hashes the local summary and registry; they do not hash or authenticate remote content.

### Bibliography inclusion and display contract

The registry accepts HTTPS references only from the reviewed NASA/USDA domains and the explicitly allowlisted DOI resolver, IJACSA publisher, UTEC institutional repository, IAF proceedings distributor, IEEE Xplore, and Analog Devices. Each entry carries a stable source ID, publication metadata, suggested citation, evidence category, mapped summary claims, module scope, reuse status, and known limitations where available. The References view displays the complete registry; prevention, radiation, and space-weather pages filter by module tags so an agriculture or EVA paper is not presented as support for an unrelated claim. DOI resolution and peer-review status are bibliographic signals, not proof that a study is clinically applicable or operationally validated.

The T-EVA share URL is not used as a citation; the canonical DOI and publisher PDF are listed. The 2024 IAF record is cited with “et al.” because the UTEC and proceedings product metadata disagree on co-author names/order; verify the original proceedings title page before publishing the full author list. The 2023 Barreto micro-review is tagged for agriculture/mechatronics only. NASA's current Volume 2 Revision F record is kept separate from OCHMO-TB-050, which is based on Revision E and explicitly reference-only.

## Evidence limitations

- Web search and retrieval smoke checks are not systematic reviews, evidence grading, or clinical validation.
- Publication metadata and a hash confirm file integrity, not the truth or currency of a claim.
- Some linked NASA evidence reports have older publication dates; users should follow the live HRP catalogue for revisions.
- NASA standards apply through program-specific tailoring and should not be reimplemented from a simplified UI summary.
- No radiation unit in this app is interpreted as safe/unsafe, a permissible-exposure-limit status, health risk, flight eligibility, or need for EVA action.
- No DONKI notification is represented as an authorized personal warning or background push alert.
