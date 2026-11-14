from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'engine/vigile/structured_facts.py';s=p.read_text(encoding='utf8');s=s.replace("without_date=(rf'(?:El valor registrado de {v} fue|{v} se registró en) {x} {u}' if language=='es' else rf'(?:The recorded value of {v} was|{v} was recorded as) {x} {u}')", "without_date=(rf'(?:El valor registrado de {v} fue|(?:La |El |la |el )?(?i:{v}) se registró en) {x} {u}' if language=='es' else rf'(?:The recorded value of {v} was|(?:The |the )?(?i:{v}) was recorded as) {x} {u}')")
p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/clinical_api.py';s=p.read_text(encoding='utf8');s=s.replace('from .clinical_models import','from pydantic import AwareDatetime\nfrom .models import Model,Id\nclass ClinicalContext(Model):\n    evaluation_id:Id\n    subject_id:Id\n    mission_id:Id\n    as_of:AwareDatetime\n    input_hash:str\n\nfrom .clinical_models import',1)
anchor="    @app.get('/clinical/evaluations/{identifier}/differential'"
pos=s.index(anchor)
s=s[:pos]+'''    @app.get('/clinical/evaluations/{identifier}/context',response_model=ClinicalContext)
    def evidence_context(identifier:str):
        r=engine.store.get('clinical_evaluation',identifier)
        return {'evaluation_id':identifier,'subject_id':r['subject_id'],'mission_id':r['mission_id'],'as_of':r['snapshot']['request']['as_of'],'input_hash':r['input_hash']}
'''+s[pos:];p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/local_assistant.py';s=p.read_text(encoding='utf8');s=s.replace("evaluations/[A-Za-z0-9_.:-]+(?:/replay)?", "evaluations/[A-Za-z0-9_.:-]+(?:/(?:replay|context))?")
anchor="    evaluation=reader.get('/clinical/evaluations/'+evaluation_id)";s=s.replace(anchor,anchor+"\n    if getattr(inference,'structured_explanations',False):\n        evaluation.update(reader.get('/clinical/evaluations/'+evaluation_id+'/context'))")
p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/voice_api.py';s=p.read_text(encoding='utf8');s=s.replace('def approved_text(result,evaluations,language):','def approved_text(result,evaluations,language,previous=()):')
anchor="            labels=[('missing_required'";pos=s.index(anchor)
s=s[:pos]+'''            prior=next((old['results'].get(condition) for old in previous if condition in old['results']),None)
            if prior and prior.get('required_for_protocol_safety')!=r.get('required_for_protocol_safety'):
                old_fields=', '.join(names.get(f,(f,f))[es] for f in prior.get('required_for_protocol_safety',[])) or ('ninguno' if es else 'none')
                parts.append(('Pendientes de seguridad en la evaluación anterior: ' if es else 'Protocol safety data pending in the previous evaluation: ')+old_fields+'.')
                parts.append(('Los estados de criterios y autorización se informan por separado; nuevos datos no autorizan tratamiento.' if es else 'Criteria and authorization states remain separate; additional data do not authorize treatment.'))
'''+s[pos:]
anchor="        try:\n            text,kind=approved_text(result,evaluations,body.language)";assert anchor in s
s=s.replace(anchor,"""        context={k:record[k] for k in ('subject_id','mission_id','as_of') if k in record}
        previous=[]
        if body.monitoring_id and record.get('previous_run_id'):
            old=reader.get('/monitoring/cycles/'+record['previous_run_id']);previous=list(old.get('clinical_evaluations',{}).values())
        if body.evaluation_id:
            context=reader.get('/clinical/evaluations/'+body.evaluation_id+'/context')
            if record.get('parent_id'):previous=[reader.get('/clinical/evaluations/'+record['parent_id'])]
        result.setdefault('explanation_context',{**context,'target_id':body.monitoring_id or body.evaluation_id})
        try:
            text,kind=approved_text(result,evaluations,body.language,previous)""")
p.write_text(s,encoding='utf8')