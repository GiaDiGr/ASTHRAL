from pathlib import Path
p=Path(__file__).resolve().parents[2]/'engine/vigile/web/app.js';s=p.read_text(encoding='utf8')
start=s.index('async function loadSubject()');end=s.index('\nfunction renderMetrics()',start)
segment=s[start:end];old='}catch(e){message(e.message);}}';assert segment.count(old)==1
segment=segment.replace(old,'}catch(e){if(generation===loadGeneration)message(e.message);}}')
s=s[:start]+segment+s[end:];p.write_text(s,encoding='utf8')
