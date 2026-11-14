from pathlib import Path
import zipfile,hashlib,json
ROOT=Path(__file__).resolve().parents[2];dest=ROOT/'work/v100/v011-runtime';dest.mkdir(exist_ok=False)
with zipfile.ZipFile(ROOT/'docs/v100/before-v100.zip') as z:z.extractall(dest)
for p in ['docs/clinical/deep-research-report-2026-10-16.md','01_INFORMES/REPORTE_CONSOLIDADO_COMPLETO.md','docs/v07/README.md','docs/v07/CONTRACTS.md','docs/v08/sources/ADA2026-short-excerpt.txt']:
 target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/p).read_bytes())
# Exact input selection preserved; only avoid parsing records that were always discarded.
p=ROOT/'engine/vigile/monitoring.py';s=p.read_text(encoding='utf8');old="rows=self.store.db.execute('SELECT kind,id,payload FROM records ORDER BY seq').fetchall()";new="rows=self.store.db.execute(\"SELECT kind,id,CASE WHEN kind='monitoring_run' THEN json_remove(payload,'$.replay_records') ELSE payload END AS payload FROM records WHERE kind!='mission_frame' ORDER BY seq\").fetchall()";assert s.count(old)==1;s=s.replace(old,new);p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/service.py';s=p.read_text(encoding='utf8');old="rows=self.store.db.execute('SELECT kind,id,payload FROM records ORDER BY kind,id').fetchall()";new="rows=self.store.db.execute(\"SELECT kind,id,payload FROM records WHERE kind IN ('measurement','baseline','baseline_withdrawal','profile','mission','mission_context','device') ORDER BY kind,id\").fetchall()";assert s.count(old)==1;s=s.replace(old,new);p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/mission_frames.py';s=p.read_text(encoding='utf8');old="return [FrameIndex.model_validate(r['index']).model_dump(mode='json') for r in engine.store.all('mission_frame')\n            if r['scope']=={'subject_id':subject_id,'mission_id':mission_id}]";new="""import json
    with engine.store.lock:
        rows=engine.store.db.execute(\"SELECT json_extract(payload,'$.index') FROM records WHERE kind='mission_frame' AND json_extract(payload,'$.scope.subject_id')=? AND json_extract(payload,'$.scope.mission_id')=? ORDER BY seq\",(subject_id,mission_id)).fetchall()
    return [FrameIndex.model_validate(json.loads(r[0])).model_dump(mode='json') for r in rows]""";assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf8')