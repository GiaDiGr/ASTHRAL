from pathlib import Path
import json,sqlite3
root=Path(__file__).resolve().parents[2]
for folder in sorted((root/'engine/data').glob('v011-development-*')):
    c=sqlite3.connect((folder/'vigile.sqlite3').as_uri()+'?mode=ro',uri=True,timeout=1)
    print(folder.name,c.execute('select kind,count(*) from records group by kind').fetchall())
    c.close()
p=root/'docs/v011/fallback-probes-v010.json'
v=json.loads(p.read_text(encoding='utf8'))
print('probe report keys',list(v))
rows=v.get('rows',[])
if rows: print(json.dumps(rows[0],ensure_ascii=True)[:5000])
