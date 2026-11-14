from pathlib import Path
p=Path(__file__).resolve().parents[2]/'engine/vigile/web/app.js';s=p.read_text(encoding='utf8')
s=s.replace("let selectedCycleId=null,operationModeState='FULL';","let selectedCycleId=null,operationModeState='FULL',missionFrames=[];")
s=s.replace("const chosen=frames.some(f=>f.id===remembered)?remembered:frames.at(-1)?.id||'';","missionFrames=frames;const chosen=remembered===''&&$('mission-frame').dataset.initialized===scopeKey?'':frames.some(f=>f.id===remembered)?remembered:frames.at(-1)?.id||'';$('mission-frame').dataset.initialized=scopeKey;")
s=s.replace("if(dashboard.evaluations.some(e=>e.id===old))$('evaluation').value=old;renderMetrics();", "if(dashboard.evaluations.some(e=>e.id===old))$('evaluation').value=old;else if(dashboard.evaluations.length){const priority={EMERGENCY:3,URGENT:2,PROMPT:1,ROUTINE:0};$('evaluation').value=[...dashboard.evaluations].sort((a,b)=>Date.parse(b.as_of)-Date.parse(a.as_of)||(priority[b.urgency]||0)-(priority[a.urgency]||0))[0].id;}renderMetrics();")
s=s.replace("$('mission-frame').onchange=loadSubject;","$('mission-frame').onchange=()=>{selected=null;loadSubject();};")
s=s.replace("const askWithEvidence=ask;ask=async function(question){await askWithEvidence(question);};","")
s=s.replace("target.replaceChildren(el('p',answer.message,'caption'));","target.replaceChildren(el('p',answer.message,'caption'));if(answer.failure_trace)target.append(el('p','Sin explicación aceptada · '+answer.failure_trace.category+' · '+answer.failure_trace.code,'caption'));")
s=s.replace("HUMAN_PLAN_RECORDED:'Plan humano registrado'","HUMAN_PLAN_RECORDED:'Plan registrado · en simulación no acredita revisión humana'")
s=s.replace("}catch(e){message(e.message);}}\n\n", "}catch(e){message(e.message);}}\n\n") # unrelated handlers are intentionally unchanged
old="function selectCycle(){selectedCycleId=$('monitoring-cycle').value;"
new="function selectCycle(){const frame=missionFrames.find(f=>f.monitoring_id===$('monitoring-cycle').value);if(frame&&frame.id!==$('mission-frame').value){$('mission-frame').value=frame.id;selected=null;loadSubject();return;}selectedCycleId=$('monitoring-cycle').value;"
assert old in s;s=s.replace(old,new)
s=s.replace("technical(parent,'Resultado verificable',result);}catch(e){message(e.message);}}","technical(parent,'Resultado verificable',result);}catch(e){if(context===loadGeneration&&evaluation===selected?.id&&cycle===selectedCycleId)message(e.message);}}")
p.write_text(s,encoding='utf8')
