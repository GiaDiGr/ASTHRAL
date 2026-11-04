"""Bounded desktop compute policy. Does not select clinical rules or priorities."""
from dataclasses import dataclass
import ctypes,os,statistics,subprocess,time,json
from ctypes import wintypes

@dataclass(frozen=True)
class ComputePolicy:
 context_tokens:int
 threads:int
 output_tokens:int
 document_limit:int
 keep_alive:str
 timeout_seconds:int

POLICIES={'FULL':ComputePolicy(6144,8,700,3,'5m',60),'LOW_POWER':ComputePolicy(2048,4,300,1,'30s',45),'CRITICAL':ComputePolicy(0,0,0,1,'0',0)}

def available_memory_bytes():
 if os.name!='nt':return None
 class Memory(ctypes.Structure):
  _fields_=[('length',wintypes.DWORD),('load',wintypes.DWORD)]+[(k,ctypes.c_ulonglong) for k in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
 m=Memory();m.length=ctypes.sizeof(m)
 return m.available if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) else None

def admit_inference(mode,minimum_available_bytes=512*1024**2):
 if mode not in POLICIES:raise ValueError('INVALID_MODE')
 if mode=='CRITICAL':return {'available':False,'reason':'CRITICAL_LLM_DISABLED'}
 free=available_memory_bytes()
 if free is not None and free<minimum_available_bytes:return {'available':False,'reason':'MEMORY_PRESSURE_LLM_SKIPPED','available_memory_bytes':free}
 return {'available':True,'reason':'RESOURCE_ADMISSION_OK','available_memory_bytes':free}

def summarize(values):
 values=list(values);out={'n':len(values),'raw':values}
 if len(values)>=5:out['median']=statistics.median(values)
 if len(values)>=20:out['p95']=sorted(values)[int(.95*(len(values)-1))];out['percentile_method']='nearest lower rank'
 return out

def process_resources(pid):
 if os.name!='nt':return {'pid':pid,'available':False}
 class PMC(ctypes.Structure):
  _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(s,ctypes.c_size_t) for s in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage']]
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
 kernel.OpenProcess.restype=wintypes.HANDLE;kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.CloseHandle.argtypes=[wintypes.HANDLE]
 psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(PMC),wintypes.DWORD];kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
 handle=kernel.OpenProcess(0x410,False,pid)
 if not handle:return {'pid':pid,'available':False}
 try:
  counter=PMC();counter.cb=ctypes.sizeof(counter)
  if not psapi.GetProcessMemoryInfo(handle,ctypes.byref(counter),ctypes.sizeof(counter)):return {'pid':pid,'available':False}
  ts=[wintypes.FILETIME() for _ in range(4)];kernel.GetProcessTimes(handle,*[ctypes.byref(t) for t in ts])
  return {'pid':pid,'working_set_bytes':counter.WorkingSetSize,'private_bytes':counter.PrivateUsage,'cpu_seconds':sum((t.dwHighDateTime<<32)+t.dwLowDateTime for t in ts[2:])/1e7}
 finally:kernel.CloseHandle(handle)

def telemetry(pids=()):
 data={'monotonic':time.perf_counter(),'available_ram_bytes':available_memory_bytes(),'processes':[process_resources(p) for p in pids],'energy':'NOT_MEASURED'}
 try:
  r=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu,utilization.memory','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  values=[int(v.strip()) for v in r.stdout.strip().split(',')];data['gpu_global']=dict(zip(['vram_used_MiB','gpu_utilization_percent','memory_utilization_percent'],values))
 except (OSError,ValueError,subprocess.TimeoutExpired):data['gpu_global']={'available':False}
 return data

def release_model(url,model):
 # Explicit operator action, separate from CRITICAL evaluation. Never stops the runtime.
 from .local_assistant import OllamaInference
 import httpx
 OllamaInference(url,model)
 with httpx.Client(trust_env=False,timeout=30,follow_redirects=False) as c:
  r=c.post(url.rstrip('/')+'/api/generate',json={'model':model,'keep_alive':0});r.raise_for_status()
  last={}
  for _ in range(40):
   r=c.get(url.rstrip('/')+'/api/ps');r.raise_for_status();last=r.json()
   if not any(m.get('name')==model for m in last.get('models',[])):return {'released':True,'loaded':last}
   time.sleep(.25)
 return {'released':False,'loaded':last}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('command',choices=['telemetry','release']);p.add_argument('--url',default='http://127.0.0.1:8891');p.add_argument('--model',default='vigile-qwen3-4b:latest');a=p.parse_args()
 print(json.dumps(telemetry([os.getpid()]) if a.command=='telemetry' else release_model(a.url,a.model),indent=2))
