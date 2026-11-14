"""Optional public bibliography retrieval. No Engine, reader, private-question or model access.
Only registered topic IDs cross this boundary; remote text never enters LLM prompts.
"""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
from urllib.parse import urlencode
import hashlib,json,ssl,socket,http.client,ipaddress,time,threading,queue,re
from pydantic import Field,StrictBool,StrictInt
from .models import Model

TOPICS={
 'cardiovascular':{'label':'Spaceflight cardiovascular deconditioning','query':'spaceflight cardiovascular deconditioning'},
 'muscle_bone':{'label':'Spaceflight muscle and bone countermeasures','query':'spaceflight muscle bone loss countermeasures'},
 'sleep_fatigue':{'label':'Spaceflight sleep and fatigue research','query':'spaceflight sleep fatigue research'},
 'radiation':{'label':'Space radiation health research','query':'space radiation astronaut health research'},
 'hyperglycemic_consensus':{'label':'2024 hyperglycemic crises consensus report','query':'Hyperglycemic Crises in Adults With Diabetes 2024 consensus report'},
}
Topic=Literal['cardiovascular','muscle_bone','sleep_fatigue','radiation','hyperglycemic_consensus']
HOST='eutils.ncbi.nlm.nih.gov'
class OnlinePolicy(Model):
 enabled:StrictBool=False
 providers:list[Literal['pubmed']]=Field(default_factory=lambda:['pubmed'],max_length=1)
 timeout_seconds:float=Field(default=4,ge=.5,le=10)
 max_response_bytes:StrictInt=Field(default=131072,ge=1024,le=131072)
 max_results:StrictInt=Field(default=3,ge=1,le=3)
 queries_per_minute:StrictInt=Field(default=2,ge=1,le=2)
 retries:StrictInt=Field(default=1,ge=0,le=1)
 cache_ttl_seconds:StrictInt=Field(default=86400,ge=60,le=86400)
class ScienceRequest(Model):topic_id:Topic
class PublicDocument(Model):
 origin:Literal['REMOTE_UNREVIEWED']='REMOTE_UNREVIEWED'
 provider:Literal['pubmed']='pubmed'
 topic_id:Topic
 title:str=Field(min_length=1,max_length=500)
 publisher:str=Field(min_length=1,max_length=200)
 url:str
 pmid:str=Field(pattern=r'^[0-9]{1,10}$')
 doi:str|None=None
 publication_date:str=Field(min_length=1,max_length=50)
 retrieved_at:str
 version:Literal['NCBI_PUBMED_ESUMMARY_V2']='NCBI_PUBMED_ESUMMARY_V2'
 excerpt:str=Field(min_length=1,max_length=500)
 excerpt_kind:Literal['TITLE_METADATA_ONLY_NOT_FULL_TEXT']='TITLE_METADATA_ONLY_NOT_FULL_TEXT'
 content_hash:str
 review_status:Literal['NOT_CLINICALLY_REVIEWED']='NOT_CLINICALLY_REVIEWED'
 limitations:list[str]=Field(default_factory=lambda:['NOT_PATIENT_GUIDANCE','PUBLICATION_DATE_IS_NOT_AUTHORITY','NOT_ELIGIBLE_FOR_RULE_UPDATES','NO_CLAIM_OF_FULL_TEXT_REVIEW'])

def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def public_addresses(host,timeout):
 if host!=HOST:raise ValueError('DESTINATION_NOT_APPROVED')
 q=queue.Queue(maxsize=1)
 def resolve():
  try:q.put(socket.getaddrinfo(host,443,type=socket.SOCK_STREAM))
  except OSError as e:q.put(e)
 threading.Thread(target=resolve,daemon=True).start()
 try:answer=q.get(timeout=timeout)
 except queue.Empty:raise TimeoutError('DNS_TIMEOUT') from None
 if isinstance(answer,Exception):raise OSError('DNS_UNAVAILABLE') from None
 addresses=list(dict.fromkeys(row[4][0] for row in answer))
 if not addresses or any((not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast) for ip in addresses):raise ValueError('NONPUBLIC_DESTINATION')
 return addresses
class PublicHTTPS(http.client.HTTPSConnection):
 def __init__(self,deadline):
  self.deadline=deadline;super().__init__(HOST,443,timeout=max(.01,deadline-time.monotonic()),context=ssl.create_default_context())
 def connect(self):
  addresses=public_addresses(self.host,max(.01,self.deadline-time.monotonic()))
  if time.monotonic()>=self.deadline:raise TimeoutError('DEADLINE')
  raw=socket.create_connection((addresses[0],443),timeout=max(.01,self.deadline-time.monotonic()))
  try:
   raw.settimeout(max(.01,self.deadline-time.monotonic()));self.sock=self._context.wrap_socket(raw,server_hostname=HOST)
  except Exception:raw.close();raise
class PubMedTransport:
 def __init__(self):self.calls=0;self.last=0.;self.lock=threading.Lock()
 def get(self,utility,params,deadline,maximum):
  allowed={'esearch.fcgi':{'db','term','retmode','retmax','sort','tool'},'esummary.fcgi':{'db','id','retmode','version','tool'}}
  if utility not in allowed or set(params)!=allowed[utility] or params['db']!='pubmed' or params['tool']!='ASTHRAL':raise ValueError('PUBLIC_REQUEST_SCHEMA')
  if utility=='esearch.fcgi' and params['term'] not in {v['query'] for v in TOPICS.values()}:raise ValueError('PUBLIC_TOPIC_ONLY')
  if utility=='esummary.fcgi' and not re.fullmatch(r'[0-9]{1,10}(,[0-9]{1,10}){0,2}',params['id']):raise ValueError('PUBLIC_IDENTIFIER_ONLY')
  with self.lock:
   wait=max(0,.4-(time.monotonic()-self.last))
   if time.monotonic()+wait>=deadline:raise TimeoutError('RATE_BUDGET')
   if wait:time.sleep(wait)
   self.last=time.monotonic();self.calls+=1
   connection=PublicHTTPS(deadline)
   try:
    connection.request('GET','/entrez/eutils/'+utility+'?'+urlencode(params),headers={'Accept':'application/json','Accept-Encoding':'identity','User-Agent':'ASTHRAL-Research/1.0 (public bibliography only)'})
    response=connection.getresponse()
    if response.status!=200:raise OSError('PROVIDER_HTTP_'+str(response.status)) # Never follow redirects.
    if 'application/json' not in response.getheader('Content-Type','').lower() or response.getheader('Content-Encoding','identity')!='identity':raise ValueError('RESPONSE_TYPE')
    length=response.getheader('Content-Length')
    if length and (not length.isdigit() or int(length)>maximum):raise ValueError('RESPONSE_TOO_LARGE')
    payload=bytearray()
    while True:
     remaining=deadline-time.monotonic()
     if remaining<=0:raise TimeoutError('DEADLINE')
     if connection.sock:connection.sock.settimeout(remaining)
     chunk=response.read(min(4096,maximum+1-len(payload)))
     if not chunk:break
     payload.extend(chunk)
     if len(payload)>maximum:raise ValueError('RESPONSE_TOO_LARGE')
    return json.loads(payload.decode('utf8'))
   finally:connection.close()

INSTRUCTIONS=re.compile(r'ignore.{0,30}(instructions|rules)|system prompt|reveal.{0,30}(secret|token)|<script|\[INST\]|role\s*:\s*system|https?://(?:localhost|127\.)',re.I)
class HybridRetrieval:
 def __init__(self,policy=None,mode=None,cache_dir=None,transport=None,clock=time.monotonic,wall=None):
  self.policy=OnlinePolicy.model_validate(policy or {});self.mode=mode or (lambda:'CRITICAL');self.transport=transport or PubMedTransport();self.clock=clock;self.wall=wall or (lambda:datetime.now(timezone.utc));self.epoch=0;self.lock=threading.Lock();self.busy=threading.Lock();self.calls=[];self.events=[]
  self.cache_dir=Path(cache_dir).resolve() if cache_dir else None
  if self.cache_dir:self.cache_dir.mkdir(parents=True,exist_ok=True)
 def mode_changed(self):
  with self.lock:self.epoch+=1
 def status(self):return {'local_origin':'LOCAL_PINNED','online_enabled_by_trusted_configuration':self.policy.enabled,'mode':self.mode(),'approved_providers':self.policy.providers,'network_permitted':self.policy.enabled and self.mode()=='FULL' and 'pubmed' in self.policy.providers,'topics':[{'id':k,'label':v['label']} for k,v in TOPICS.items()],'remote_authority':'REMOTE_UNREVIEWED','no_private_context_accepted':True}
 def _current(self,epoch):return self.mode()=='FULL' and self.policy.enabled and self.epoch==epoch
 def _cache(self,topic):
  if not self.cache_dir:return None
  p=self.cache_dir/(topic+'.json')
  try:
   if p.is_symlink() or not p.resolve().is_relative_to(self.cache_dir) or p.stat().st_size>16384:return None
   row=json.loads(p.read_text(encoding='utf8'));docs=[PublicDocument.model_validate(d).model_dump(mode='json') for d in row['documents']]
   if set(row)!={'topic_id','stored_at','documents','hash'} or row['topic_id']!=topic or len(docs)>3 or any(d['topic_id']!=topic for d in docs):return None
   for d in docs:
    check_document(d)
   if row['hash']!=fingerprint([topic,row['stored_at'],docs]):return None
   age=(self.wall()-datetime.fromisoformat(row['stored_at'])).total_seconds()
   return (docs,age) if 0<=age<=7*86400 else None
  except (OSError,ValueError,KeyError,TypeError):return None
 def _store(self,topic,docs):
  if not self.cache_dir:return
  at=self.wall().isoformat();row={'topic_id':topic,'stored_at':at,'documents':docs,'hash':fingerprint([topic,at,docs])};raw=json.dumps(row,ensure_ascii=False)
  if len(raw.encode())>16384:return
  path=self.cache_dir/(topic+'.json')
  if path.is_symlink():return
  temp=self.cache_dir/(topic+'.tmp');
  if temp.is_symlink():return
  temp.write_text(raw,encoding='utf8');temp.replace(path)
 def retrieve(self,topic):
  start=self.clock();epoch=self.epoch
  def result(status,reason,documents=(),delivery='NONE'):
   row={'status':status,'reason':reason,'local_origin':'LOCAL_PINNED','remote_origin':'REMOTE_UNREVIEWED','topic_id':topic if isinstance(topic,str) and topic in TOPICS else None,'documents':list(documents),'delivery':delivery,'elapsed_ms':round((self.clock()-start)*1000,3),'model_invocations':0,'clinical_decisions_changed':False}
   self.events.append({k:row[k] for k in ('status','reason','topic_id','elapsed_ms','delivery')});self.events=self.events[-32:];return row
  if topic is None:return result('LOCAL_ONLY','NO_PUBLIC_TOPIC_SELECTED')
  if not isinstance(topic,str) or topic not in TOPICS:return result('LOCAL_ONLY','PUBLIC_TOPIC_NOT_APPROVED')
  if not self._current(epoch) or 'pubmed' not in self.policy.providers:return result('LOCAL_ONLY','ONLINE_DISABLED_OR_MODE_NOT_FULL')
  if not self.busy.acquire(False):return result('REMOTE_UNAVAILABLE','RETRIEVAL_BUSY')
  try:
   cached=self._cache(topic)
   if cached and cached[1]<=self.policy.cache_ttl_seconds:return result('REMOTE_OPTIONAL','PUBLIC_CACHE_HIT',cached[0],'CACHE_NOT_LIVE') if self._current(epoch) else result('LOCAL_ONLY','MODE_CHANGED')
   now=self.clock();self.calls=[t for t in self.calls if now-t<60]
   if len(self.calls)>=self.policy.queries_per_minute:return result('REMOTE_UNAVAILABLE','PUBLIC_QUERY_RATE_LIMIT')
   self.calls.append(now);deadline=time.monotonic()+self.policy.timeout_seconds;docs=None
   for attempt in range(self.policy.retries+1):
    try:
     if not self._current(epoch):return result('LOCAL_ONLY','MODE_CHANGED')
     search=self.transport.get('esearch.fcgi',{'db':'pubmed','term':TOPICS[topic]['query'],'retmode':'json','retmax':str(self.policy.max_results),'sort':'relevance','tool':'ASTHRAL'},deadline,self.policy.max_response_bytes)
     ids=search['esearchresult']['idlist']
     if not isinstance(ids,list) or len(ids)>self.policy.max_results or any(not isinstance(x,str) or not re.fullmatch(r'[0-9]{1,10}',x) for x in ids) or len(set(ids))!=len(ids):raise ValueError('INVALID_PUBLIC_IDS')
     if not ids:docs=[];break
     if not self._current(epoch):return result('LOCAL_ONLY','MODE_CHANGED')
     summary=self.transport.get('esummary.fcgi',{'db':'pubmed','id':','.join(ids),'retmode':'json','version':'2.0','tool':'ASTHRAL'},deadline,self.policy.max_response_bytes)
     docs=[]
     for pmid in ids:
      v=summary['result'][pmid]
      if str(v.get('uid'))!=pmid:raise ValueError('IDENTIFIER_MISMATCH')
      title=v['title'].strip();publisher=v['fulljournalname'].strip();date=v['pubdate'].strip()
      if INSTRUCTIONS.search(title):continue
      doi=next((x['value'] for x in v.get('articleids',[]) if x.get('idtype')=='doi'),None)
      if doi is not None and not re.fullmatch(r'10\.[0-9]{4,9}/[^\s<>"\x00-\x1f]{1,180}',doi):raise ValueError('INVALID_DOI')
      document=PublicDocument(topic_id=topic,title=title,publisher=publisher,url='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/',pmid=pmid,doi=doi,publication_date=date,retrieved_at=self.wall().isoformat(),excerpt=title,content_hash='pending').model_dump(mode='json')
      document['content_hash']=fingerprint({k:v for k,v in document.items() if k!='content_hash'});check_document(document);docs.append(document)
     break
    except (OSError,TimeoutError):
     if attempt>=self.policy.retries or time.monotonic()>=deadline:break
    except (ValueError,KeyError,TypeError,AttributeError):
     docs=None;break
   if not self._current(epoch):return result('LOCAL_ONLY','MODE_CHANGED')
   if docs is None:
    if cached:return result('REMOTE_OPTIONAL','PROVIDER_UNAVAILABLE_CACHED_UNREVIEWED',cached[0],'STALE_CACHE_NOT_LIVE')
    return result('REMOTE_UNAVAILABLE','PROVIDER_UNAVAILABLE_OR_RESPONSE_REJECTED')
   with self.lock:
    if not self._current(epoch):return result('LOCAL_ONLY','MODE_CHANGED')
    try:self._store(topic,docs)
    except OSError:pass # A full/read-only cache never interrupts local clinical work.
   return result('REMOTE_OPTIONAL','PUBLIC_REFERENCES_RETRIEVED' if docs else 'NO_PUBLIC_RESULTS',docs,'LIVE')
  finally:self.busy.release()

def check_document(d):
 if d['url']!='https://pubmed.ncbi.nlm.nih.gov/'+d['pmid']+'/' or d['excerpt']!=d['title'] or INSTRUCTIONS.search(d['excerpt']):raise ValueError('INVALID_PUBLIC_DOCUMENT')
 at=datetime.fromisoformat(d['retrieved_at'])
 if at.tzinfo is None:raise ValueError('RETRIEVAL_TIMEZONE_REQUIRED')
 if d['content_hash']!=fingerprint({k:v for k,v in d.items() if k!='content_hash'}):raise ValueError('PUBLIC_DOCUMENT_HASH')