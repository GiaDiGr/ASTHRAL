from pathlib import Path
import json,statistics,collections
D=Path(r'C:\Users\Gianni\Desktop\Vigile\docs/v09')
metrics={}
for name in ['audit-before.json','audit-final-full.json','audit-after-low.json','audit-after-critical.json']:
 report=json.loads((D/name).read_text(encoding='utf8'));out={}
 for k in (3,5):
  p=[];rec=[]
  for row in report['rag']:
   found=row['retrieved'][:k];gold=set(row['query']['relevant_document_paths']);p.append(sum(b['reference']['document'] in gold for b in found)/k);rec.append(len({b['reference']['document'] for b in found}&gold)/len(gold))
  out[str(k)]={'document_path_precision_per_fragment_rank':statistics.mean(p),'document_coverage':statistics.mean(rec),'fragment_precision':report['summary']['rag_macro'][str(k)]['fragment_precision'],'fragment_coverage':report['summary']['rag_macro'][str(k)]['fragment_recall']}
 metrics[name]=out
before=json.loads((D/'rag-benchmark-before.json').read_text());compute=json.loads((D/'compute-benchmark.json').read_text());after=compute['rag'];same=all(a['ids']==b['ids'] for a,b in zip(before['rows'],after['rows']))
perf={'rag_before_ms':before['median_ms'],'rag_after_ms':after['timing_ms']['median'],'rag_top5_same_48_queries':same,'rag_speed_ratio':before['median_ms']/after['timing_ms']['median'],'llm':{},'clinical_batch_ms':compute['clinical']['scenario_batch_ms'],'measurement_ms':json.loads((D/'measurement-benchmark.json').read_text())['timing_ms']}
for name,mode in compute['modes'].items():
 loaded=mode['ollama_ps_after']['models'];perf['llm'][name]={'cold_seconds_n1':mode['requests'][0]['seconds'],'warm':mode['warm_seconds'],'reported_vram_bytes':loaded[0]['size_vram'] if loaded else 0,'reported_context_tokens':loaded[0]['context_length'] if loaded else None}
resources=json.loads((D/'resources-profiles.json').read_text())
profiles={}
for name,data in resources['profiles'].items():
 ps={};cpu=[]
 for row in data['rows']:
  for p in row['processes']:
   if 'working_set_bytes' in p:ps[str(p['pid'])]={'peak_working_set_bytes':max(ps.get(str(p['pid']),{}).get('peak_working_set_bytes',0),p['working_set_bytes']),'peak_private_bytes':max(ps.get(str(p['pid']),{}).get('peak_private_bytes',0),p['private_bytes'])}
 for a,b in zip(data['rows'],data['rows'][1:]):
  old={p['pid']:p for p in a['processes']};delta=sum(max(0,p['cpu_seconds']-old[p['pid']]['cpu_seconds']) for p in b['processes'] if p['pid'] in old and 'cpu_seconds' in p and 'cpu_seconds' in old[p['pid']]);cpu.append(100*delta/(b['monotonic']-a['monotonic'])/32)
 profiles[name]={'per_pid':ps,'samples':len(data['rows']),'peak_total_machine_cpu_percent_observed':max(cpu) if cpu else None,'peak_global_gpu_percent_observed':max(x['gpu_global'].get('gpu_utilization_percent',0) for x in data['rows'])}
perf['resources_profiles']=profiles
(D/'rag-metrics.json').write_text(json.dumps({'annotation':'12 fixed narrow passage queries; path precision counts retrieved fragments belonging to a labelled document, fragment precision counts only labelled exact passage IDs; does not measure relevance of every corpus passage','reports':metrics},indent=2),encoding='utf8')
(D/'performance-summary.json').write_text(json.dumps(perf,indent=2),encoding='utf8')
print(json.dumps({'rag':metrics['audit-final-full.json'],'cache_same':same,'profiles':profiles},indent=2))
