from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'));D=R/'docs/v101-ux'
freeze=json.loads((R/'docs/v101/CODE_FREEZE.json').read_text(encoding='utf8'))
assert all(hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in freeze['files'])
assert hashlib.sha256((R/'docs/v101/candidate-code-v101.zip').read_bytes()).hexdigest()==freeze['sha256']
checkpoint=json.loads((R/'docs/v101/checkpoint.json').read_text(encoding='utf8'))
assert hashlib.sha256((R/'docs/v100/candidate-code-r2.zip').read_bytes()).hexdigest()==checkpoint['r2_code_archive_sha256']
from vigile.local_protection import verified_backup,restrict_directory
backup=verified_backup(R/'engine/data/mission-v101-final/vigile.sqlite3',R/'work/v101-ux/v101-db-backup');restrict_directory(R/'work/v101-ux/v101-db-backup')
(D/'checkpoint.json').write_text(json.dumps({'v101_archive_sha256':freeze['sha256'],'r2_archive_sha256':checkpoint['r2_code_archive_sha256'],'all_v101_frozen_files_match_before_changes':True,'original_databases_unmodified':True,'v101_backup':backup},indent=2),encoding='utf8')
from vigile.registry import Registry
registry=Registry(R)
ids=['C001','C002','C003','C005','C012','C014','C015','C019','C032']
# Presentation-only exact excerpts; not executable clinical rules or new science.
data={cid:{'name':registry.get('conditions',cid)['catalog_record']['name_specialty'],'context':registry.get('conditions',cid)['catalog_record']['description_spaceflight'],'source_ids':registry.get('conditions',cid)['source_ids']} for cid in ids}
data['sources']={sid:registry.get('sources',sid) for sid in sorted({s for cid in ids for s in data[cid]['source_ids']})}
(D/'guide-source-excerpts.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf8')
web=R/'engine/vigile/web'
p=web/'index.html';s=p.read_text(encoding='utf8');needle='<div id="persistent-clinical-alert"';assert needle in s
s=s.replace(needle,'<section id="journey" class="card journey" aria-label="Recorrido de salud"><h2>Tu recorrido de salud</h2><p id="journey-context" role="status">Selecciona astronauta y checkpoint.</p><div id="journey-links" class="journey-links"></div><div id="journey-evaluation"></div></section>'+needle,1);p.write_text(s,encoding='utf8')
p=web/'app.js';s=p.read_text(encoding='utf8')
s=s.replace("'episodes','replay-results'])empty(id)","'episodes','replay-results','journey-links','journey-evaluation'])empty(id)")
s=s.replace("$('updated').textContent='Cargando el contexto seleccionado…'","$('journey-context').textContent='Cargando contexto; no se muestran relaciones de la vista anterior.';$('updated').textContent='Cargando el contexto seleccionado…'")
old="const baseline=dashboard.baselines.find(b=>b.variable===$('variable').value);"
assert old in s
new="const cycleIndicator=currentCycle()?.domains.flatMap(d=>d.indicators).find(i=>i.variable===$('variable').value);const comparison=cycleIndicator?.baseline_comparison;const baseline=comparison&&cycleIndicator.unit===rows[0].unit?{value:comparison.baseline_value}:null;if(new Set(rows.map(r=>r.unit)).size!==1){container.textContent='Unidades heterogéneas: no se combinan en una gráfica. Consulta los valores y unidades de cada muestra.';return;}"
s=s.replace(old,new,1)
# Graph baseline comes only from the selected cycle's actual comparison, never all visible baselines.
p.write_text(s,encoding='utf8')
p=web/'management.js';s=p.read_text(encoding='utf8')
a=s.index(' const vars=dashboard.measurements.map');b=s.index(' const rows=',a)
s=s[:a]+" const cycle=currentCycle();const vars=(cycle?.domains||[]).flatMap(d=>d.indicators).filter(i=>i.value!==null&&i.state==='DESCRIPTIVE_AVAILABLE').map(i=>i.variable);const has=prefix=>vars.some(v=>v.startsWith(prefix));\n const relevant=new Set([...(has('physiology.vo2')?['C001']:[]),...(has('physiology.strength')?['C002']:[]),...(has('bone.')?['C003']:[]),...(dashboard.mission.phase==='POST_MISSION'?['C005']:[]),...(has('sleep.')?['C012','C013']:[]),...(has('behavior.fatigue')?['C014']:[]),...(has('radiation.')?['C032']:[])]);\n"+s[b:]
s+='\n// Exact public catalogue excerpts, frozen for presentation. Not new clinical knowledge.\nconst astronautGuideCatalogue='+json.dumps(data,ensure_ascii=False)+';\n'
s+='''
const indicatorTopics={'physiology.vo2max':['C001'],'physiology.strength':['C002'],'bone.hip_bmd':['C003'],'bone.lumbar_bmd':['C003'],'sleep.duration':['C012'],'sleep.efficiency':['C012'],'behavior.fatigue_score':['C014'],'cognition.reaction_time':['C015'],'immune.viral_load':['C019'],'radiation.interval_effective_dose':['C032'],'radiation.career_spaceflight':['C032']};
Object.assign(names,{'bone.hip_bmd':'Densidad mineral ósea · cadera','bone.lumbar_bmd':'Densidad mineral ósea · lumbar','radiation.interval_effective_dose':'Dosis efectiva del intervalo','radiation.career_spaceflight':'Dosis efectiva espacial acumulada','sleep.efficiency':'Eficiencia del sueño','cognition.reaction_time':'Tiempo de reacción','behavior.fatigue_score':'Puntuación de fatiga','immune.viral_load':'Carga viral del analito declarado',NOT_MEASURED:'No medido',CONFLICTING_DATA:'Datos contradictorios',CURRENT_MISSION_PHASE_MISMATCH:'Fase de medición incompatible con el ciclo',MEASUREMENT_TOO_OLD:'Medición desactualizada'});
function guideButton(text,action){const b=el('button',text,'secondary');b.type='button';b.onclick=action;return b;}
function guideScope(){return dashboard?dashboard.profile.id+'/'+dashboard.profile.mission_id:null;}
function guideCycle(){const c=currentCycle();return c&&c.subject_id===dashboard.profile.id&&c.mission_id===dashboard.profile.mission_id?c:null;}
function evaluationOrigin(id){return (dashboard?.monitoring||[]).find(c=>c.subject_id===dashboard.profile.id&&c.mission_id===dashboard.profile.mission_id&&Object.values(c.clinical_evaluations||{}).some(e=>e.id===id));}
async function openCycleEvaluation(id,cycleId){
 const origin=evaluationOrigin(id);if(!origin||origin.id!==cycleId){message('No hay vínculo explícito entre esa evaluación y el ciclo.');return;}
 const frame=missionFrames.find(f=>f.monitoring_id===cycleId);const scope=guideScope();
 if(frame&&frame.id!==$('mission-frame').value){$('mission-frame').value=frame.id;selected=null;await loadSubject();if(guideScope()!==scope||$('mission-frame').value!==frame.id)return;}
 if(!dashboard?.evaluations.some(e=>e.id===id)){message('La evaluación no está disponible en este checkpoint.');return;}
 selectedCycleId=cycleId;$('evaluation').value=id;renderEvaluation();showView('clinical');
}
function renderJourney(){
 const host=$('journey-links'),context=$('journey-context'),evaluation=$('journey-evaluation');if(!host||!dashboard)return;host.replaceChildren();evaluation.replaceChildren();
 const cycle=guideCycle();const frame=dashboard.historical_frame;
 context.textContent=label(dashboard.profile.id)+' · '+label(dashboard.profile.mission_id)+' · '+(frame?'Checkpoint: '+frame.id:'Vista actual de datos recibidos')+(cycle?' · ciclo: '+cycle.id+' · '+cycle.as_of:' · sin ciclo de monitorización verificable');
 for(const [text,view] of [['1. Mediciones y tendencias','monitoring'],['2. Hallazgos registrados','monitoring'],['3. Evaluación y manejo','clinical'],['4. Seguimiento','followup']])host.append(guideButton(text,()=>{showView(view);if(text.startsWith('2.'))$('findings').parentElement.open=true;}));
 const origin=selected&&evaluationOrigin(selected.id);
 if(selected)evaluation.append(el('p','Evaluación seleccionada: '+selected.id+' · '+selected.as_of+' · '+label(selected.urgency)+'. '+(origin?.id===cycle?.id?'Pertenece explícitamente a este ciclo.':'Contexto distinto o sin vínculo explícito con el ciclo mostrado; no se combinan sus resultados.')));
 if(origin&&origin.id!==cycle?.id)evaluation.append(guideButton('Ir al ciclo de origen de esta evaluación',()=>openCycleEvaluation(selected.id,origin.id)));
 for(const e of Object.values(cycle?.clinical_evaluations||{}))if(dashboard.evaluations.some(row=>row.id===e.id))evaluation.append(guideButton('Ver '+label(e.condition_id||Object.keys(e.results||{})[0])+' de este ciclo',()=>openCycleEvaluation(e.id,cycle.id)));
 if(!Object.keys(cycle?.clinical_evaluations||{}).length)evaluation.append(el('p','Este ciclo no contiene una evaluación clínica enlazada. Sus tendencias no se convierten en diagnóstico ni tratamiento.','caption'));
}
function renderAstronautGuidance(){
 const container=$('space-monitoring');if(!container||!dashboard)return;document.getElementById('astronaut-guidance')?.remove();const group=el('section');group.id='astronaut-guidance';group.append(el('h3','Entender mis indicadores y la prevención documentada'));
 const cycle=guideCycle();if(!cycle){group.append(el('p','Sin ciclo verificable para este astronauta y misión; interpretación no disponible.'));container.append(group);return;}
 group.append(el('p','Resultados del ciclo '+cycle.id+' · '+cycle.as_of+'. Descripción e información documental; no órdenes personalizadas ni autorizadas.'));
 for(const domain of cycle.domains){
  const section=el('details');section.append(el('summary',label(domain.domain)+' · datos, incertidumbre y orientación'));
  for(const i of domain.indicators){
   const card=el('div',undefined,'indicator-guide');const usable=i.value!==null&&i.state==='DESCRIPTIVE_AVAILABLE';card.append(el('h4',label(i.variable)),el('p','Qué se midió: '+(usable?displayNumber(i.value)+' '+i.unit:'Sin valor utilizable: '+label(i.state))+'. Fuente de muestra: '+(i.latest_measurement_id||'sin muestra')+'.'));
   card.append(el('p',usable?'Significado: valor descriptivo del motor, no diagnóstico ni confirmación de normalidad.':'El dato ausente, inválido, contradictorio o desactualizado no se considera normal ni demuestra recuperación.'));
   const b=i.baseline_comparison;card.append(el('p',usable&&b?'Baseline utilizado: '+b.baseline_id+' = '+displayNumber(b.baseline_value)+' '+i.unit+'. Cambio: '+displayNumber(b.absolute_change)+' '+i.unit+' · descriptivo.':'Sin comparación utilizable con baseline personal en este ciclo; no se estima ni se imputa.'));
   if(usable&&i.trend&&Number.isFinite(i.trend.slope_per_day))card.append(el('p','Tendencia calculada: '+displayNumber(i.trend.slope_per_day)+' '+i.unit+'/día. No predice evolución clínica ni selecciona tratamientos.'));
   card.append(el('p','Incertidumbre y condiciones: '+[...(i.limitations||[]),...(domain.limitations||[]),...(i.quality_issues||[]).map(q=>q.reason)].map(label).join(' · '),'caption'));
   const ids=indicatorTopics[i.variable]||[];
   if(!ids.length)card.append(el('p','Sin relación específica de prevención mapeada para este indicador; no se deduce una enfermedad por pertenecer a este sistema.'));
   for(const cid of ids){const entry=astronautGuideCatalogue[cid];card.append(el('p','Biblioteca relacionada (no diagnóstico ni causalidad en tu caso): '+entry.name+'. '+entry.context));const doc=(dashboard.countermeasure_documents||[]).find(d=>d.condition_id===cid);
    if(usable&&doc){const d=el('details');d.append(el('summary','Prevención o mejora documentada · '+cid),el('p','Condiciones: plan y protocolo de misión autorizado, revisión humana y medición comparable. Recursos específicos no verificados para esta contramedida; no se presume disponibilidad de equipos.'),el('p','No hay pauta individual, agenda, dosis ni autorización generadas.'),el('p',doc.text),el('small','Fuentes del catálogo: '+doc.source_ids.join(', ')));technical(d,'Estado documental de cada etapa y limitaciones',doc);card.append(d);}else card.append(el('p',usable?'No hay contramedida específica aprobada e integrada para este indicador en esta vista. Se mantiene la limitación.':'Orientación personalizada no evaluable con este dato. El catálogo de referencia no es una acción indicada para este ciclo.'));
    const sources=el('details');sources.append(el('summary','Referencias documentales · '+entry.source_ids.join(', ')));for(const sid of entry.source_ids){const source=astronautGuideCatalogue.sources[sid];sources.append(el('p',sid+' · '+source.source));technical(sources,'Registro original '+sid,source);}card.append(sources);
   }
   if(i.normative_finding_id){const finding=dashboard.findings.find(f=>f.id===i.normative_finding_id);card.append(el('p',finding?'Hallazgo normativo asociado explícitamente: '+finding.id+'. Incumplimiento normativo no equivale a diagnóstico.':'Hallazgo referenciado, no incluido en la proyección actual.'));if(finding)technical(card,'Hallazgo exacto y trazabilidad',finding);}
   section.append(card);
  }
  group.append(section);
 }
 group.append(guideButton('Ver episodios y planes de seguimiento registrados',()=>showView('followup')),el('p','Sólo consulta: no se crean pruebas, recordatorios, ejercicios ni tratamientos. Un plan pendiente no acredita recuperación.','caption'));container.append(group);
}
const renderMonitoringBeforeAstronaut=renderMonitoring;renderMonitoring=function(){renderMonitoringBeforeAstronaut();renderAstronautGuidance();renderJourney();};
const renderEvaluationBeforeAstronaut=renderEvaluation;renderEvaluation=function(){renderEvaluationBeforeAstronaut();renderJourney();};$('evaluation').onchange=renderEvaluation;
'''
p.write_text(s,encoding='utf8')
p=web/'style.css'
with p.open('a',encoding='utf8') as f:f.write('\n.journey{margin:16px 0}.journey-links{display:flex;flex-wrap:wrap;gap:8px}.journey button{white-space:normal;text-align:left}.indicator-guide{border-top:1px solid #dedbe6;padding:12px 0}.indicator-guide h4{margin:8px 0}.indicator-guide p{line-height:1.6}.indicator-guide details{margin:10px 0}#astronaut-guidance{overflow-wrap:anywhere}\n')
print('Preserved archives/backup and applied presentation-only integration changes')