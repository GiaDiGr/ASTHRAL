import os,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'engine'))
from vigile.store import Store
from vigile.service import Engine
from vigile.registry import Registry
from vigile.monitoring import MonitoringService
from vigile.clinical_engine import ClinicalService
root=Path(os.environ['VIGILE_CORPUS']);s=Store(root/'engine/data/backups/v0100-before-v011/vigile.sqlite3')
try:
 e=Engine(Registry(root),s);assert e.implementation_hash=='c896211d20b52ade1279aeb306421891f5e29b542f910074d542321c4b815db9'
 result={'implementation_hash':e.implementation_hash,'clinical':[ClinicalService(e).replay(r['id']) for r in s.all('clinical_evaluation')],'monitoring':[MonitoringService(e).replay(r['id']) for r in s.all('monitoring_run')],'audit':s.verify()}
 assert all(r['matches'] for r in result['clinical']+result['monitoring']) and result['audit']
 (root/'docs/v011/archived-v010-replays.json').write_text(json.dumps(result,indent=2));print('Archived v010: all 39 replays match')
finally:s.close()
