from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
# Safe, project-authored English retrieval notes; not a new clinical guideline.
D=R/'docs/knowledge';D.mkdir(exist_ok=True)
notes='''# ASTHRAL local knowledge: scope and existing evidence

ASTHRAL means Astronaut Support Tool for Health Risk Assessment and Logistics. It is an offline-first astronaut health monitoring and medical decision-support research prototype. Structured clinical outcomes come exclusively from the deterministic engine, never from retrieved text, Internet sources, or the language model. Clinical execution remains blocked and no verified mission medical authorization policy is implemented.

## Recorded measurements, baselines, and trends

A personal baseline is a documented comparison reference built from eligible observations under an identified protocol. A descriptive change in aerobic capacity, measured strength, sleep duration, or other indicator does not establish clinical worsening, normality, recovery, or a diagnosis. Missing, invalid, conflicting, or out-of-date measurements remain insufficient evidence. Measurement method, units, anatomical site, acquisition quality, mission phase, gravity, observation window, and receipt checkpoint affect whether comparison is possible. A graph must use the baseline actually compared by the selected cycle and must not combine heterogeneous units silently.

## DKA data sufficiency and independent safety

The stored diabetic ketoacidosis evaluation distinguishes diagnostic criteria from protocol safety. AND/OR alternatives must be evaluated as a tree. A missing alternative is not automatically required when another valid branch already satisfies its criterion. In a stored assessment, missing_required, optional_not_measured, invalid_required, and required_for_protocol_safety have different meanings. Potassium safety restrictions remain independent of whether diagnostic criteria are met. Bicarbonate and urine ketones must not be described as mandatory when other valid acidosis and ketosis alternatives have already satisfied the recorded criteria. These statements describe the existing engine contract; they are not instructions to diagnose or treat a person. Consult the pinned clinical criteria and primary sources before independent medical review.

## Seven implemented pathways and documented management

The existing pathways cover diabetes, diabetic ketoacidosis, hypoglycemia in adults with diabetes, orthostatic hypotension, POTS, acute kidney injury, and anaphylaxis. A differential assessment is a set of hypotheses, not a probability or a signed diagnosis. Meeting computed criteria does not constitute independent clinical confirmation. Urgency, confirmation, protocol eligibility, resource availability, and treatment status are separate states. Documentary interventions, synthetic resource manifests, and human-reported follow-up do not authorize administration, demonstrate execution, or verify efficacy. Insulin-specific potassium restrictions must not be represented as a general contraindication of all DKA support. In suspected anaphylaxis, stored emergency priority must remain visible even when criteria are incomplete or resources are unavailable.

## Spaceflight cardiovascular, muscle, and bone monitoring

The existing catalogue documents cardiovascular deconditioning, changes in aerobic performance, muscle strength, and bone health in reduced-gravity contexts. These links are documentary context and do not establish a causal diagnosis for an individual astronaut. Existing reference outlines discuss authorized exercise or mission countermeasure plans; ASTHRAL does not generate an exercise prescription, assume equipment availability, or replace mission review. DXA and laboratory capability are not assumed available in flight. Standing-test interpretations cannot be transferred automatically to free microgravity. Recovery and follow-up require the appropriate gravity context and comparable measurements.

## Sleep, fatigue, cognition, immune markers, and radiation

Recorded sleep duration, sleep efficiency, fatigue scales, reaction-time tests, viral measurements, and radiation records require their original methods, units, timing, and context. A fatigue score must match its declared scale. A PCR trend alone is not a reactivation diagnosis. Dosimetric exposure is not a cancer diagnosis, and a recorded interval total is not a lifetime dose. The application does not create individual cancer predictions, SANS treatments, universal spaceflight thresholds, medication adjustments for microgravity, or new preventive schedules. Where evidence, resources, or an approved countermeasure mapping are absent, the limitation remains explicit.

## Local and supplementary scientific references

LOCAL_PINNED means a local document with fixed provenance; it does not itself declare clinical validation. REMOTE_UNREVIEWED means public scientific reference metadata retrieved online and not approved to update rules. Publication date is not a measure of medical authority. The public PubMed adapter can retrieve title metadata and stable PMIDs for approved general topics only. It never receives astronaut records, identifiers, measurements, private questions, voice, tokens, or clinical context. External results remain in a separate panel and never enter the clinical evidence guard or LLM prompt. Cached remote references remain unreviewed, timestamped, and separate from the approved corpus. FULL requires explicit trusted online enablement; LOW_POWER and CRITICAL initiate no external retrieval.

## Scientific attribution and review boundaries

Clinical source metadata and precise criterion versions remain in engine/vigile/clinical_knowledge/sources_verified.json and its hash-pinned manifest. Existing primary references include the 2024 hyperglycemic crises consensus, WAO anaphylaxis guidance, KDIGO acute kidney injury definitions, orthostatic/POTS references, and the cited ADA standards. Spaceflight bibliography remains in 07_EVIDENCIAS/fuentes.json. Citation metadata is not a redistribution license for a full article. This project-authored implementation note does not replace any primary source, resolve pending clinical disagreements, or add treatment criteria. Human clinical, operational, flight, physical microphone, and visual acceptance remain independent of software tests.
'''
(D/'ASTHRAL_LOCAL_KNOWLEDGE.md').write_text(notes,encoding='utf8')
p=R/'engine/vigile/knowledge_v08.py';s=p.read_text(encoding='utf8');s=s.replace('SOURCES=[','SOURCES=[\n (\'docs/knowledge/ASTHRAL_LOCAL_KNOWLEDGE.md\',\'IMPLEMENTATION_DOCUMENTATION_NOT_GUIDELINE\',\'1.1.0\'),',1);p.write_text(s,encoding='utf8')
# Build a separate English-only, redistributable pinned manifest using the existing builder.
from vigile import knowledge_v08 as k
original=k.SOURCES;k.SOURCES=[original[0]]
summary=k.build(R,R/'engine/local_ai/library-asthral.json');k.SOURCES=original
print('English local library blocks:',summary['blocks'])
# Current metadata changes are explicit; historical documents remain untouched.
for name in ['api.py','portal.py']:
 p=R/'engine/vigile'/name;s=p.read_text(encoding='utf8').replace("version='1.0.1'","version='1.1.0'").replace("'version':'1.0.1'","'version':'1.1.0'");p.write_text(s,encoding='utf8')
# Robust handling of invalid topic objects in the no-network path.
p=R/'engine/vigile/hybrid_retrieval.py';s=p.read_text(encoding='utf8').replace("topic if topic in TOPICS else None","topic if isinstance(topic,str) and topic in TOPICS else None");p.write_text(s,encoding='utf8')