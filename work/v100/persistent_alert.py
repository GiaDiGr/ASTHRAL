from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'engine/vigile/web/index.html';s=p.read_text(encoding='utf8');anchor='<section id="general"';assert anchor in s;s=s.replace(anchor,'<div id="persistent-clinical-alert" class="persistent-alert" role="alert" aria-live="assertive" hidden></div>'+anchor,1);p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/web/app.js';s=p.read_text(encoding='utf8');s=s.replace("$('updated').textContent='Cargando el contexto seleccionado…';","$('persistent-clinical-alert').hidden=true;$('persistent-clinical-alert').textContent='';$('updated').textContent='Cargando el contexto seleccionado…';",1)
s=s.replace('function selectCycle(){','function selectCycle(){',1)
s += '''
// A registered critical priority stays visible while using voice/assistant views.
function renderPersistentAlert(){const banner=$('persistent-clinical-alert');if(!dashboard){banner.hidden=true;return;}const cycle=currentCycle();const states=Object.values(cycle?.event_states||{});const urgencies=[selected?.urgency,...Object.values(cycle?.clinical_evaluations||{}).map(e=>e.urgency),...states.filter(s=>s.state!=='CRITERIA_NOT_MET'&&s.state!=='NOT_APPLICABLE').map(s=>s.urgency)];const urgency=urgencies.includes('EMERGENCY')?'EMERGENCY':urgencies.includes('URGENT')?'URGENT':null;banner.hidden=!urgency;banner.textContent=urgency?'SIMULACIÓN · Prioridad registrada por el motor: '+label(urgency)+'. Revisa evaluación e historial. Un aviso previo no se cierra automáticamente por ausencia de datos. No es un diagnóstico firmado ni autorización de tratamiento.':'';banner.dataset.target=cycle?.id||selected?.id||'';}
const renderBeforePersistentAlert=renderEvaluation;renderEvaluation=function(){renderBeforePersistentAlert();renderPersistentAlert();};$('evaluation').onchange=renderEvaluation;
'''
s=s.replace('renderOverview();updateAssistantContext();}', 'renderOverview();updateAssistantContext();renderPersistentAlert();}')
p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/web/style.css';p.write_text(p.read_text(encoding='utf8')+'\n.persistent-alert{border:2px solid #a63e3e;background:#fff1f0;color:#842929;border-radius:10px;padding:14px;margin:16px 0;font-size:13px;line-height:1.6;overflow-wrap:anywhere}\n',encoding='utf8')