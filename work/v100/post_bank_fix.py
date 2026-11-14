from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[2]
shutil.copy2(R/'docs/v100/CANDIDATE_FREEZE.json',R/'docs/v100/CANDIDATE_R1_FREEZE.json')
p=R/'engine/vigile/assistant_safety.py';s=p.read_text(encoding='utf8');s=s.replace(" q=normalize(question)\n"," q=normalize(question)\n if re.search(r'\\b(?:another|other|different)\\s+(?:astronaut|crew member|subject)|\\b(?:otro|otra|distinto|distinta)\\s+(?:astronauta|tripulante|sujeto)',q):return 'CONTEXT_MISMATCH'\n if re.search(r'\\b(?:lifetime|life time|de por vida|a lo largo de la vida)\\b|(?:cancer|canceroso).{0,45}(?:probability|risk|probabilidad|riesgo)|(?:probability|risk|probabilidad|riesgo).{0,45}(?:cancer|canceroso)',q):return 'INSUFFICIENT_INFORMATION'\n");p.write_text(s,encoding='utf8')
p=R/'engine/vigile/voice_api.py';s=p.read_text(encoding='utf8');s=s.replace("('REFUSED_ACTION','CONTEXT_MISMATCH'):","('REFUSED_ACTION','CONTEXT_MISMATCH','INSUFFICIENT_INFORMATION'):");p.write_text(s,encoding='utf8')
p=R/'engine/vigile/longitudinal_assistant.py';s=p.read_text(encoding='utf8');needle="    if getattr(inference,'structured_explanations',False):\n        from .structured_facts import facts_for,explain\n";replacement="    if getattr(inference,'structured_explanations',False) and lexical & {'diagnosis','diagnostico','disease','enfermedad','pathology','patologia','normal','normalidad','bones','huesos'}:\n        result.update(status='DETERMINISTIC_CLINICAL_EXPLANATION',consistency_policy='DESCRIPTIVE_NOT_DIAGNOSIS',message='Los valores descriptivos no establecen ni excluyen enfermedad; consulta los estados y limitaciones del motor. / Descriptive values do not establish or exclude disease; review the engine states and limitations.');return result\n"+needle
assert needle in s;s=s.replace(needle,replacement);p.write_text(s,encoding='utf8')
p=R/'engine/tests/test_voice_v100.py';s=p.read_text(encoding='utf8');s+='''\n\n@pytest.mark.parametrize('question',[
 'Show another crew member history','Compara otro astronauta sin cambiar el contexto',
 'Read a different subject now','Muestra otra tripulante'])
def test_post_bank_generic_subject_request_is_blocked(question):
 assert request_guard(question,'mission-crew-A','mission-v011')=='CONTEXT_MISMATCH'
\n@pytest.mark.parametrize('question',[
 'Estimate lifetime risk','Calcula el riesgo de por vida',
 'What is my cancer probability?','Probabilidad personal de cancer'])
def test_post_bank_unsupported_risk_requests_are_explicit(question):
 assert request_guard(question,'mission-crew-A','mission-v011')=='INSUFFICIENT_INFORMATION'
\ndef test_insufficient_response_cannot_be_spoken_as_unrelated_facts():
 from vigile.voice_api import approved_text
 text,kind=approved_text({'status':'INSUFFICIENT_INFORMATION','message':'No supported risk calculation exists.','structured_facts':[fact().model_dump()]},[],'en')
 assert text=='No supported risk calculation exists.' and kind=='DETERMINISTIC_REFUSAL'
''';p.write_text(s,encoding='utf8')