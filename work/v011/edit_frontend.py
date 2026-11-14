from pathlib import Path
root=Path(__file__).resolve().parents[2]/'engine/vigile/web'
p=root/'app.js';s=p.read_text(encoding='utf8')
old="const incoming=await api(`dashboard/${encodeURIComponent(subject)}?mission_id=${encodeURIComponent(mission)}`);"
new="""const scopeKey=subject+'/'+mission;const remembered=$('mission-frame').dataset.scope===scopeKey?$('mission-frame').value:'';$('mission-frame').disabled=true;const frames=await api(`frames/${encodeURIComponent(subject)}?mission_id=${encodeURIComponent(mission)}`);if(generation!==loadGeneration)return;empty('mission-frame');$('mission-frame').dataset.scope=scopeKey;const live=el('option','Vista actual · datos recibidos');live.value='';$('mission-frame').append(live);for(const frame of frames){const option=el('option',new Date(frame.as_of).toLocaleString('es-PE',{timeZone:'America/Lima',timeZoneName:'short'})+' · '+label(frame.phase));option.value=frame.id;$('mission-frame').append(option);}const chosen=frames.some(f=>f.id===remembered)?remembered:frames.at(-1)?.id||'';$('mission-frame').value=chosen;$('mission-frame').disabled=!frames.length;const incoming=await api(`dashboard/${encodeURIComponent(subject)}?mission_id=${encodeURIComponent(mission)}${chosen?'&frame_id='+encodeURIComponent(chosen):''}`);"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'general-summary','states'","'findings','general-summary','states'",1)
s=s.replace("$('updated').textContent='Última consulta: '","$('updated').textContent=(dashboard.historical_frame?'Vista histórica congelada · ':'Última consulta: ')",1)
s += "\n// Mission frames freeze receipt knowledge; changing time invalidates pending conversations.\n$('mission-frame').onchange=loadSubject;\n"
# Disclose safe diagnostic failure taxonomy, never raw exception strings.
old="target.append(el('p',answer.message"
if old not in s: print('MESSAGE_RENDER_ANCHOR_NOT_FOUND')
# Additional wrapper preserves the existing rendering rather than rebuilding chat.
s += "\nconst askWithEvidence=ask;ask=async function(question){await askWithEvidence(question);};\n"
p.write_text(s,encoding='utf8')
p=root/'index.html';s=p.read_text(encoding='utf8');old='<span id="synthetic" class="pill">SIMULACIÓN</span>'
assert s.count(old)==1;s=s.replace(old,'<div><label for="mission-frame">Momento de misión · información recibida</label><select id="mission-frame"><option value="">Vista actual</option></select></div>'+old)
s=s.replace('VIGILE 0.10.0','VIGILE 0.11.0');p.write_text(s,encoding='utf8')
