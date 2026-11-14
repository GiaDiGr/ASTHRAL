from pathlib import Path
import sqlite3,json
db=Path(__file__).resolve().parents[2]/'engine/data/v011-development-02/vigile.sqlite3'
c=sqlite3.connect(db)
for row in c.execute("select payload from records where kind='monitoring_run' and id in ('mission-crew-B-cycle-18','mission-crew-B-cycle-18p1')"):
    r=json.loads(row[0]);ev=r['clinical_evaluations']['DKA'];a=ev['results']['DKA']
    print(r['id'],json.dumps({k:a[k] for k in ('diagnostic_status','data_issues','missing_required','optional_not_measured','invalid_required','required_for_protocol_safety','space_applicability','evaluation_tree')},indent=2))
    print('obs',ev.get('observations'))
c.close()
