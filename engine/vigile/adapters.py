"""Versioned synthetic file adapter and small loopback HTTP client. No dependencies added."""
import json,time,urllib.parse
import httpx
from pathlib import Path
from typing import Protocol,Iterable
from .models import Measurement
from .simulator import SyntheticDataset

class MeasurementSource(Protocol):
    def measurements(self) -> Iterable[Measurement]: ...

class SyntheticAdapter:
    def __init__(self,dataset): self.dataset=SyntheticDataset.model_validate(dataset)
    @classmethod
    def from_file(cls,path):
        with Path(path).open('rb') as stream: raw=stream.read(10*1024*1024+1)
        if len(raw)>10*1024*1024: raise ValueError('DATASET_TOO_LARGE')
        return cls(SyntheticDataset.model_validate_json(raw))
    def measurements(self): return iter(self.dataset.measurements)
    def submit(self,client):
        # Entire envelope validated before the first network write; a failed request stops the import.
        client.call('POST','/missions',self.dataset.mission.model_dump(mode='json'))
        client.call('POST','/profiles',self.dataset.profile.model_dump(mode='json'))
        for d in self.dataset.devices: client.call('POST','/devices',d.model_dump(mode='json'))
        return [client.call('POST','/measurements',m.model_dump(mode='json')) for m in self.measurements()]

class LocalClient:
    def __init__(self,base_url,token,record_synthetic_transcript=False):
        u=urllib.parse.urlsplit(base_url)
        if u.scheme!='http' or u.hostname!='127.0.0.1' or u.username or u.password or u.query or u.fragment or u.path not in ('','/'):
            raise ValueError('EXPLICIT_LOOPBACK_URL_REQUIRED')
        self.base_url=base_url.rstrip('/'); self._token=token
        self.transport=httpx.Client(timeout=30,trust_env=False,follow_redirects=False)
        self.transport_retries=0
        self.timings=[]; self.transcript=[]; self.record_synthetic_transcript=record_synthetic_transcript
    def call(self,method,path,body=None,expected=None):
        if not path.startswith('/') or path.startswith('//'): raise ValueError('RELATIVE_API_PATH_REQUIRED')
        headers={'Authorization':'Bearer '+self._token,'Content-Type':'application/json'}
        raw=None if body is None else json.dumps(body,allow_nan=False).encode()
        start=time.perf_counter()
        try:
            response=self.transport.request(method,self.base_url+path,content=raw,headers=headers)
        except httpx.RemoteProtocolError:
            if method!='GET':raise
            self.transport_retries+=1
            response=self.transport.request(method,self.base_url+path,content=raw,headers={**headers,'Connection':'close'})
        status=response.status_code; result=response.json()
        self.timings.append({'method':method,'path':path.split('?')[0],'status':status,'milliseconds':1000*(time.perf_counter()-start)})
        # This client is used for synthetic demos. Do not enable transcripts for clinical records.
        if self.record_synthetic_transcript:
            self.transcript.append({'method':method,'path':path,'request':body,'status':status,'response':result})
        if expected is not None and status!=expected or expected is None and not 200<=status<300:
            raise RuntimeError('HTTP_'+str(status)+' '+method+' '+path.split('?')[0])
        return result

    def close(self): self.transport.close()
