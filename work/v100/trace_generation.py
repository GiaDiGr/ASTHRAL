from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'engine/vigile/structured_facts.py';s=p.read_text(encoding='utf8');line="    t=time.perf_counter();obj,metrics=inference._complete([{'role':'system','content':system},{'role':'user','content':json.dumps({'question':question,'facts':public},ensure_ascii=False)}],schema,400)";assert line in s
s=s.replace(line,"    t=time.perf_counter()\n    try:obj,metrics=inference._complete([{'role':'system','content':system},{'role':'user','content':json.dumps({'question':question,'facts':public},ensure_ascii=False)}],schema,400)\n    except Exception as exc:\n        exc.vigile_stage='STRUCTURED_GENERATION';raise")
p.write_text(s,encoding='utf8')