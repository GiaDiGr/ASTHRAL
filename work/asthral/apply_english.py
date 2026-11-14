from pathlib import Path
import json,re,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'));W=R/'engine/vigile/web';M=json.loads((R/'work/asthral/translations-en.json').read_text(encoding='utf8'))
pattern=re.compile('|'.join(re.escape(k) for k in sorted(M,key=len,reverse=True)))
for name in ['app.js','management.js','voice-controller.js']:
 p=W/name;s=p.read_text(encoding='utf8');s=pattern.sub(lambda m:M[m.group()],s).replace("'es-PE'","'en-US'").replace("'sí'","'yes'")
 if name=='app.js':
  s=s.replace("||'es'","||'en'")
  s=s.replace("n.textContent=String(text)","n.textContent=englishDisplayText(String(text))")
  s=s.replace('JSON.stringify(value,null,2)','JSON.stringify(englishDisplayValue(value),null,2)')
  # Add only the approved topic ID; neither context nor raw questions reach the provider.
  s=s.replace('history_context_id:',"public_topic:document.getElementById('science-topic')?.value||null,history_context_id:")
  # Existing ask receives the local result; display supplementary science independently.
  s=s.replace("const title=el('h3',answer.generated", "renderScientificReferences(answer.supplementary_science);const title=el('h3',answer.generated")
  s=s.replace("empty('chat-answer');document.getElementById('chart-values')", "empty('chat-answer');document.getElementById('science-results')?.replaceChildren();document.getElementById('chart-values')")
  s=s.replace("operationModeState=status.assistant.mode||'FULL';", "if(document.getElementById('science-status'))document.getElementById('science-status').textContent=status.scientific_retrieval?.network_permitted?'Local Knowledge · Online Scientific Retrieval Enabled':'Local Knowledge · Online Retrieval Disabled';operationModeState=status.assistant.mode||'FULL';")
 p.write_text(s,encoding='utf8')
# Exact translations of the previously published countermeasure outlines; no source mutation.
from vigile.registry import Registry
r=Registry(R)
translations={
'C001':'Prevention: authorized countermeasure program [ES:S04]. Monitoring: comparable VO2max [ES:S01]. Quality: verify units, method, baseline, and EVA context. Detection: apply 32.9/36.5 and 80% only where applicable [ES:S01]. Assessment: review symptoms and performance. Differential: non-spaceflight and multisystem causes [RV]. Triage: mission/human review. Intervention: authorized exercise, not a generated prescription [RMA]. Recovery: reconditioning toward preflight [ES:S01]. Follow-up: longitudinal trend. Prognosis: INCONCLUSIVE for individual clinical prediction.',
'C002':'Prevention: resistance exercise [ES]. Monitoring: strength using the same muscle group and method. Quality: prevent heterogeneous comparisons. Detection: current/preflight ratio and the 80% requirement [S01]. Assessment/differential: injury, pain, nutrition, neurological causes. Triage: human review for functional decline. Intervention: authorized plan. Recovery: return toward baseline [S01]. Follow-up: repeat the test. Prognosis: no validated predictor.',
'C003':'Prevention: authorized exercise, nutrition, and countermeasures. Monitoring: scheduled DXA/QCT. Quality: consistent anatomical region and technology. Detection: 95/95/90% retention [S01]. Assessment: integrate fracture and risk, not BMD alone. Differential: metabolic causes and trauma. Triage/intervention: clinician. Recovery: reconditioning toward baseline. Follow-up: postflight monitoring. Prognosis: do not infer an individual fracture from DXA alone.',
'C005':'Prevention: countermeasures for gravity transition [S02]. Monitoring: symptoms plus heart rate and blood pressure under protocol. Quality: do not extrapolate postflight tests to microgravity. Detection: deviations under an authorized protocol. Assessment: standing/tilt testing only in a valid context. Differential: hypovolemia, arrhythmia, neurological causes. Triage: mission policy. Intervention: compression or other countermeasures only when authorized. Recovery/follow-up: reassessment in gravity. Prognosis: no autonomous predictor.',
'C012':'Prevention: scheduling, light, and environment. Monitoring: sleep duration, efficiency, and diary. Quality: valid wear time and observation windows. Detection: personal deviation, not diagnosis. Assessment/differential: workload, noise, circadian factors, mental health. Triage: functional impairment. Intervention: authorized countermeasures. Recovery/follow-up: return toward the recorded pattern. Prognosis: trend, not diagnosis.',
'C013':'Prevention: circadian scheduling. Monitoring: sleep/wake patterns and light. Quality: temporal synchronization. Detection: phase shift under a mission algorithm [RV]. Assessment/differential: schedules and sleep. Triage/intervention: authorization. Recovery/follow-up: realignment. Prognosis: research only.',
'C014':'Prevention: program-level workload limits. Monitoring: workload, sleep, and performance. Quality: complete scales and temporal alignment. Detection: multivariable combination [RV]. Assessment/differential: sleep, disease, stress. Triage: operational risk. Intervention: authorized adjustment. Recovery/follow-up: performance. Prognosis: no universal predictor.',
'C032':'Prevention: ALARA and shielding. Monitoring: dosimetry. Quality: dose type, unit, and organ. Detection: accumulation versus limits. Assessment: exposure, not cancer. Differential: not applicable for compliance. Triage: a separate radiological event. Intervention: mission-defined exposure reduction. Recovery/follow-up: career monitoring. Prognosis: independent risk models.'}
M.update({r.get('conditions',k)['clinical_pathway_profile_as_published']:v for k,v in translations.items()})
# Retain the translation memory with provenance, separate from immutable clinical knowledge.
(W/'translations-en.json').write_text(json.dumps(M,ensure_ascii=False,indent=2),encoding='utf8')
p=W/'app.js'
with p.open('a',encoding='utf8') as f:f.write('''
// English presentation never rewrites source records, clinical codes, units or numbers.
function englishDisplayText(value){
 if(typeof value!=='string')return value;
 if(window.ASTHRAL_TRANSLATIONS?.[value])return window.ASTHRAL_TRANSLATIONS[value];
 if(value.startsWith('{')||value.startsWith('[')){try{return JSON.stringify(englishDisplayValue(JSON.parse(value)),null,2);}catch{}}
 if(/[¿¡ñÑáéíóúÁÉÍÓÚ]|\\b(?:mediciones|tratamiento|autorizado|criterios|evaluación|datos|fuentes|protocolo|seguimiento|recuperación|músculo|sueño|ejercicio|potasio|bicarbonato|cetonas|reactivación)\\b/i.test(value))return 'Approved English source rendering unavailable. Original provenance is retained; no clinical interpretation has been added.';
 return value;
}
function englishDisplayValue(value){if(Array.isArray(value))return value.map(englishDisplayValue);if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,englishDisplayValue(v)]));return typeof value==='string'?englishDisplayText(value):value;}
function renderScientificReferences(result){
 const host=document.getElementById('science-results'),status=document.getElementById('science-status');if(!host||!status)return;host.replaceChildren();
 status.textContent=result?.status==='REMOTE_OPTIONAL'?'Local Knowledge + Online Scientific Sources':result?.status==='REMOTE_UNAVAILABLE'?'Local Knowledge · Connection Unavailable':'Local Knowledge · Online Retrieval Disabled';
 if(!result)return;host.append(el('p',label(result.reason)));
 for(const d of result.documents||[]){const row=el('details');row.append(el('summary','External Source — Not Clinically Reviewed'),el('p',d.title),el('p',d.publisher+' · Publication: '+d.publication_date),el('p','Last Retrieved: '+d.retrieved_at+' · '+(result.delivery==='LIVE'?'Live retrieval':'Cached reference · not a live connection')));
  // The provider returns a canonical PMID URL, never arbitrary remote navigation.
  if(/^https:\\/\\/pubmed\\.ncbi\\.nlm\\.nih\\.gov\\/[0-9]{1,10}\\/$/.test(d.url)){const link=el('a','View PubMed reference');link.href=d.url;link.target='_blank';link.rel='noopener noreferrer';row.append(link);}
  row.append(el('small','PMID '+d.pmid+(d.doi?' · DOI '+d.doi:' · DOI unavailable')+' · Title metadata only; no full-text review or treatment recommendation.'));host.append(row);
 }
}
''')
# A synchronous local translation table loads before rendering; no remote translator.
p=W/'index.html';s=p.read_text(encoding='utf8').replace('<script src="/assets/app.js"','<script src="/assets/translations.js" defer></script><script src="/assets/app.js"',1);p.write_text(s,encoding='utf8')
(W/'translations.js').write_text('window.ASTHRAL_TRANSLATIONS='+json.dumps(M,ensure_ascii=False)+';\n',encoding='utf8')
# Only explicitly reviewed static assets are served.
p=R/'engine/vigile/portal.py';s=p.read_text(encoding='utf8').replace("'management.js'):raise", "'management.js','translations.js'):raise");p.write_text(s,encoding='utf8')
p=R/'engine/vigile/api.py';s=p.read_text(encoding='utf8').replace("title='VIGILE Health Intelligence Engine'","title='ASTHRAL Health Intelligence Engine'");p.write_text(s,encoding='utf8')
p=R/'engine/pyproject.toml';s=p.read_text(encoding='utf8').replace("version = \"1.0.1\"","version = \"1.1.0\"");p.write_text(s,encoding='utf8')
print('English interface, curated source translations and separate public-science panel applied')