from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'engine/vigile/web/voice-controller.js';s=p.read_text(encoding='utf8');s=s.replace("const epoch=state.epoch;stopPlayback();status('Sintetizando", "const epoch=++state.epoch;stopTracks();state.chunks=[];stopPlayback();status('Sintetizando")
s=s.replace("window.VigileVoice={reset,accept(answer){stopPlayback();", "window.VigileVoice={reset,beforeQuestion(){state.epoch++;stopTracks();stopPlayback();state.chunks=[];state.speech=null;by('voice-play').disabled=true;status('Consulta por texto; micrófono apagado.');},accept(answer){stopTracks();stopPlayback();")
p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/web/app.js';s=p.read_text(encoding='utf8');s=s.replace('async function ask(question){const run=', 'async function ask(question){window.VigileVoice?.beforeQuestion();const run=',1);p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/voice_api.py';s=p.read_text(encoding='utf8');anchor='    for ev in evaluations:'
labels="""    state_labels={'CRITERIA_MET':('criteria met','criterios cumplidos'),'CRITERIA_NOT_MET':('criteria not met','criterios no cumplidos'),'INSUFFICIENT_DATA':('insufficient data','datos insuficientes'),'SUSPECTED':('suspected only','sólo sospecha'),'CONFLICTING_EVIDENCE':('conflicting evidence','evidencia contradictoria'),'NOT_APPLICABLE':('not applicable','no aplicable'),'EMERGENCY':('emergency','emergencia'),'URGENT':('urgent','urgente'),'PROMPT':('prompt review','evaluación pronta'),'ROUTINE':('routine','rutina'),'SATISFIED':('satisfied as a criteria state only','satisfecha sólo como estado de criterios'),'REQUIRED':('required','requerida'),'NOT_REQUIRED':('not required','no requerida'),'BLOCKED_MISSING_DATA':('blocked because data are missing','bloqueado por datos pendientes'),'BLOCKED_AUTHORIZATION':('blocked without verified authorization','bloqueado sin autorización verificada'),'BLOCKED_RESOURCE':('blocked because resources are missing','bloqueado por recursos pendientes'),'BLOCKED_CONTRAINDICATION':('blocked by safety restrictions','bloqueado por restricciones de seguridad'),'NOT_STARTED':('not started','no iniciado'),'PENDING':('pending','pendiente')}
    label=lambda code:state_labels.get(code,(code,code))[es]
"""
assert s.count(anchor)==1;s=s.replace(anchor,labels+anchor)
for field in ('diagnostic_status','urgency','confirmation_status','protocol_status','treatment_status'):
 s=s.replace('{r["'+field+'"]}','{label(r["'+field+'"]) }')
p.write_text(s,encoding='utf8')