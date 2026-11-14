from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'engine/vigile/knowledge_v08.py';s=p.read_text(encoding='utf8');start=s.index('    q=terms(question);bags=');end=s.index('    if not found:',start)
s=s[:start]+'''    from .retrieval_bm25 import rank
    ranked=rank(verified,question,cache)
    found=[];per_document={}
    for block,score in ranked:
        name=block['reference']['document']
        if per_document.get(name,0)>=2:continue
        found.append({**block,'retrieval_score':round(score,6),'retrieval_algorithm':'BM25_BILINGUAL_HEADING_1'})
        per_document[name]=per_document.get(name,0)+1
        if len(found)>=limit:break
'''+s[end:];p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/longitudinal_assistant.py';s=p.read_text(encoding='utf8');s=s.replace('def answer_monitoring(reader,inference,run_id,question,history=(),library=None):','def answer_monitoring(reader,inference,run_id,question,history=(),library=None,language="es"):')
anchor="    if result['mode']=='CRITICAL':return result";assert anchor in s
s=s.replace(anchor,'''    if getattr(inference,'structured_explanations',False) and lexical & {'criteria','criterio','protocolo','protocol','alert','alerta'}:
        result.update(status='DETERMINISTIC_CLINICAL_EXPLANATION',consistency_policy='CRITICAL_CLINICAL_FACTS_ENGINE_ONLY');return result
'''+anchor)
anchor="    result['inference_attempted']=True\n    try:";assert anchor in s
s=s.replace(anchor,'''    if getattr(inference,'structured_explanations',False):
        from .structured_facts import facts_for,explain
        facts=facts_for(run,blocks,language)
        facts.sort(key=lambda f:(-(4 if 'baseline' in query and f.baseline is not None else 0)-len(terms(f.variable)&query),f.id))
        result['structured_facts']=[f.model_dump(mode='json') for f in facts[:5]]
        if not facts:return result
        result['inference_attempted']=True
        try:result.update(explain(inference,question,facts[:5],language))
        except (httpx.HTTPError,ValueError,KeyError,TypeError,IndexError,MemoryError) as exc:
            from .inference_failures import failure_trace
            result.update(status='EXTRACTIVE_FALLBACK',generated=[],failure_trace=failure_trace(exc),message='No verifiable generated explanation; exact engine evidence retained.')
        return result
'''+anchor);p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/local_assistant.py';s=p.read_text(encoding='utf8');anchor="    if not status['available']:";assert s.count(anchor)==1
s=s.replace(anchor,"    if getattr(inference,'structured_explanations',False):\n        result.update(status='DETERMINISTIC_CLINICAL_EXPLANATION',consistency_policy='CRITICAL_CLINICAL_FACTS_ENGINE_ONLY');return result\n"+anchor);p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/inference_failures.py';s=p.read_text(encoding='utf8');s=s.replace("SECURITY = frozenset((","SECURITY = frozenset(('STRUCTURED_FACT_REALIZATION_REJECTED',");p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/assistant_safety.py';s=p.read_text(encoding='utf8');start=s.index(' if mission_id and any(');end=s.index(' return None',start)
s=s[:start]+''' if mission_id and any(x!=mission_id.lower() for x in re.findall(r'v07-mission-[a-z0-9_-]+|mission-v[0-9]+[a-z0-9_-]*',q)):return 'CONTEXT_MISMATCH'
 if subject_id:
  requested=re.findall(r'v07-crew-[abc]|mission-crew-[abc]|\\bcrew [abc]\\b|\\bastronauta? [abc]\\b',q)
  for x in requested:
   if x.startswith(('v07-crew-','mission-crew-')):
    if x!=subject_id.lower():return 'CONTEXT_MISMATCH'
   elif x[-1]!=subject_id.lower()[-1]:return 'CONTEXT_MISMATCH'
'''+s[end:];p.write_text(s,encoding='utf8')