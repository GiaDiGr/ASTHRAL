from pathlib import Path
import sys,json,time,statistics,tracemalloc,os
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.offline_library import OfflineLibrary
from vigile.hybrid_retrieval import HybridRetrieval
from vigile.space_compute import process_resources
lib=OfflineLibrary(R/'engine/local_ai/library-asthral.json');h=HybridRetrieval({'enabled':True},lambda:'FULL',R/'work/asthral/live-public-cache')
tracemalloc.start();cpu=time.process_time();local=[];cached=[]
for _ in range(30):
 start=time.perf_counter();lib.search('spaceflight cardiovascular baseline',2);local.append((time.perf_counter()-start)*1000)
for _ in range(10):
 start=time.perf_counter();row=h.retrieve('hyperglycemic_consensus');cached.append((time.perf_counter()-start)*1000);assert row['delivery']=='CACHE_NOT_LIVE'
current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
report={'scope':'Local Python retrieval process; excludes separate Ollama process and flight conditions','local_search_samples':30,'local_search_median_ms':statistics.median(local),'cached_remote_samples':10,'cached_remote_median_ms':statistics.median(cached),'cpu_seconds':time.process_time()-cpu,'python_peak_tracemalloc_bytes':peak,'process':process_resources(os.getpid()),'external_requests_during_profile':h.transport.calls,'model_requests':0,'energy_measured':False,'no_energy_savings_claim':True}
(R/'docs/asthral/performance.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='process'}))