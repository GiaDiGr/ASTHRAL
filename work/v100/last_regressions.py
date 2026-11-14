from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'engine/vigile/voice_api.py';s=p.read_text(encoding='utf8');needle="    for ev in evaluations:\n";s=s.replace(needle,"    if len(evaluations)>1:parts.append('Resumen oral: hechos descriptivos y estados clínicos urgentes; revisa también las demás rutas en pantalla.' if es else 'Spoken summary: descriptive facts and urgent clinical states; also review the other pathways on screen.')\n"+needle);p.write_text(s,encoding='utf8')
p=R/'engine/tests/test_voice_v100.py';s=p.read_text(encoding='utf8');s+='''\n\ndef test_persistent_alert_outside_hidden_cards():
 root=Path(__file__).resolve().parents[1]/'vigile/web'
 html=(root/'index.html').read_text(encoding='utf8')
 assert html.index('id="persistent-clinical-alert"')<html.index('id="general"')
 assert 'aria-live="assertive"' in html
 js=(root/'app.js').read_text(encoding='utf8')
 assert "cycle?.clinical_evaluations" in js and "renderPersistentAlert();" in js
\n\ndef test_multiple_pathways_speech_is_explicitly_a_summary():
 from vigile.voice_api import approved_text
 r={'status':'EXTRACTIVE_ONLY','generated':[],'answer':[]}
 text,_=approved_text(r,[{'results':{}},{'results':{}}],'en')
 assert 'also review the other pathways on screen' in text
''';p.write_text(s,encoding='utf8')