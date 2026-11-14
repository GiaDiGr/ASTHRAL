"""Executable synthetic HTTP integration and initial measurements; no clinical assertions."""
import os,sys,json,time,socket,secrets,hashlib,subprocess,platform,statistics
import httpx
from pathlib import Path
from datetime import datetime,timedelta,timezone
from urllib.parse import urlencode
from .simulator import generate
from .adapters import SyntheticAdapter,LocalClient
from .store import Store,digest

def deny_external_network():
    """Test guard for Python socket calls, not an OS firewall or process sandbox."""
    import ipaddress
    def check(address):
        host=address[0] if isinstance(address,tuple) else address
        try: allowed=ipaddress.ip_address(host).is_loopback
        except ValueError: allowed=host=='localhost'
        if not allowed: raise OSError('EXTERNAL_NETWORK_DISABLED_FOR_TEST')
    connect=socket.socket.connect; connect_ex=socket.socket.connect_ex; resolve=socket.getaddrinfo; sendto=socket.socket.sendto
    def guarded_connect(sock,address): check(address); return connect(sock,address)
    def guarded_connect_ex(sock,address): check(address); return connect_ex(sock,address)
    def guarded_resolve(host,*args,**kwargs): check(host); return resolve(host,*args,**kwargs)
    def guarded_sendto(sock,data,*args): check(args[-1]); return sendto(sock,data,*args)
    socket.socket.connect=guarded_connect; socket.socket.connect_ex=guarded_connect_ex
    socket.getaddrinfo=guarded_resolve; socket.socket.sendto=guarded_sendto

def process_metrics(pid):
    if sys.platform!='win32': return {'available':False,'reason':'WINDOWS_COUNTERS_ONLY'}
    import ctypes
    from ctypes import wintypes as w
    class Memory(ctypes.Structure):
        _fields_=[('cb',w.DWORD),('PageFaultCount',w.DWORD)]+[(k,ctypes.c_size_t) for k in
            ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True); psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]; kernel.OpenProcess.restype=w.HANDLE
    kernel.CloseHandle.argtypes=[w.HANDLE]
    kernel.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4
    psapi.GetProcessMemoryInfo.argtypes=[w.HANDLE,ctypes.POINTER(Memory),w.DWORD]
    handle=kernel.OpenProcess(0x410,False,pid)
    if not handle: return {'available':False,'reason':'PROCESS_COUNTER_ACCESS_FAILED'}
    try:
        memory=Memory(); memory.cb=ctypes.sizeof(memory)
        times=[w.FILETIME() for _ in range(4)]
        if not psapi.GetProcessMemoryInfo(handle,ctypes.byref(memory),memory.cb) or not kernel.GetProcessTimes(handle,*[ctypes.byref(x) for x in times]):
            return {'available':False,'reason':'PROCESS_COUNTER_READ_FAILED'}
        seconds=lambda t:((t.dwHighDateTime<<32)+t.dwLowDateTime)/1e7
        return {'available':True,'working_set_bytes':memory.WorkingSetSize,'peak_working_set_bytes':memory.PeakWorkingSetSize,
            'cpu_seconds':seconds(times[2])+seconds(times[3])}
    finally: kernel.CloseHandle(handle)

def protect_directory(directory):
    if sys.platform!='win32': directory.chmod(0o700); return
    # Exact path supplied as an argument, never interpolated into shell code.
    script="""$path=$args[0]; $identity=[System.Security.Principal.WindowsIdentity]::GetCurrent().User;
    $acl=New-Object System.Security.AccessControl.DirectorySecurity; $acl.SetOwner($identity); $acl.SetAccessRuleProtection($true,$false);
    foreach ($sid in @($identity,[System.Security.Principal.SecurityIdentifier]::new('S-1-5-18'),[System.Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))) {
      $rule=[System.Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'); $acl.AddAccessRule($rule)
    }; Set-Acl -LiteralPath $path -AclObject $acl"""
    import base64,shutil
    # Script uses an environment variable to avoid PowerShell argument parsing of paths.
    script=script.replace('$args[0]','$env:VIGILE_PRIVATE_DIRECTORY')
    env=os.environ.copy(); env.pop('PSModulePath',None); env['VIGILE_PRIVATE_DIRECTORY']=str(directory.resolve())
    subprocess.run([shutil.which('pwsh') or 'powershell','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],
        env=env,check=True,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))

def exercise(writer,reader,dataset,frontend=None):
    frontend=frontend or writer
    SyntheticAdapter(dataset).submit(writer)
    scope={'subject_id':dataset.profile.id,'mission_id':dataset.mission.id}; query=urlencode(scope)
    origin=datetime(2025,1,1,12,tzinfo=timezone.utc); end=origin+timedelta(days=90)
    iso=lambda t:t.isoformat()
    for name in ('vo2','strength'):
        writer.call('POST','/baselines',dict(id='baseline-'+name,measurement_ids=dataset.groups['preflight_'+name],
            minimum_observations=3,protocol_reference='SYNTHETIC_FIXTURE',as_of=iso(origin)))
    baseline=frontend.call('GET','/research-records/baseline/baseline-vo2')
    assert frontend.call('GET','/baselines/baseline-vo2/status?'+urlencode({'as_of':iso(end)}))['availability']=='AVAILABLE_FOR_RESEARCH'
    trend=writer.call('POST','/trends',dict(measurement_ids=dataset.groups['longitudinal_vo2'],as_of=iso(end),
        ewma_lambda=.3,cusum_target=45,cusum_allowance=1,baseline_id='baseline-vo2',max_gap_seconds=31*86400,
        policy_reference='SYNTHETIC_STATISTICAL_PARAMETERS_NOT_MEDICAL'))
    recovery=writer.call('POST','/trends',dict(measurement_ids=dataset.groups['recovery_vo2'],as_of=iso(origin+timedelta(days=120)),
        ewma_lambda=.3,cusum_target=45,cusum_allowance=1,baseline_id='baseline-vo2',policy_reference='SYNTHETIC'))
    def evaluate(rule,bindings=None,as_of=end,**kw):
        return writer.call('POST','/evaluations',dict(rule_id=rule,**scope,as_of=iso(as_of),bindings=bindings or {},mode='SIMULATION',**kw))
    aero=evaluate('VIGILE-AER-003',{'premission_aerobic_capacity':'baseline-vo2','current_aerobic_capacity':dataset.groups['longitudinal_vo2'][-1]})
    muscle=evaluate('VIGILE-MUS-002',{'baseline_strength':'baseline-strength','current_strength':dataset.groups['longitudinal_strength'][-1]})
    co2=evaluate('VIGILE-ENV-002',co2_measurement_ids=dataset.groups['co2_full'])
    for finding in (aero,muscle,co2):
        if finding['result']!='REQUIREMENT_NOT_MET': raise AssertionError(finding['result']+': '+finding.get('reason',''))
    gaps=evaluate('VIGILE-ENV-002',as_of=origin+timedelta(days=91),co2_measurement_ids=dataset.groups['co2_gap'])
    faulty=[]
    for identifier in dataset.groups['faults']:
        sample=next(m for m in dataset.measurements if m.id==identifier)
        faulty.append(evaluate('VIGILE-AER-001',{'vo2max_relative':identifier},sample.timestamp))
    postflight=evaluate('VIGILE-AER-001',{'vo2max_relative':dataset.groups['recovery_vo2'][-1]},origin+timedelta(days=120))
    if any(f['result']!='INCONCLUSIVE' for f in [gaps,postflight,*faulty]): raise AssertionError('INCONCLUSIVE_WAS_LOST')
    quality=writer.call('POST','/quality/assessments',dict(measurement_ids=dataset.groups['faults'],as_of=iso(origin+timedelta(days=120)),historical=True))
    if quality['result']!='INCONCLUSIVE': raise AssertionError('QUALITY_NOT_BLOCKED')
    # C015 is explicitly a synthetic observer record, never inferred from an invented cognitive cutoff.
    writer.call('POST','/episodes',dict(id='sim-cognition',condition_id='C015',**scope))
    note=writer.call('POST','/clinical-notes',dict(id='sim-note',episode_id='sim-cognition',observed_at=iso(end),
        kind='OBSERVATION',text='SYNTHETIC observer fixture for multisystem plumbing, no diagnosis'))
    multi=writer.call('POST','/multisystem',dict(finding_ids=[co2['id'],note['finding_id']],interaction_id='MSI06',
        max_separation_seconds=60,policy_reference='SYNTHETIC_COOCCURRENCE_WINDOW'))
    writer.call('POST','/episodes',dict(id='sim-episode',condition_id='C027',finding_ids=[co2['id']],**scope))
    for previous,target in [('FINDING','ASSESSMENT'),('ASSESSMENT','FOLLOW_UP')]:
        writer.call('POST','/episodes/sim-episode/transitions',dict(target=target,note='SYNTHETIC human workflow',expected_state=previous))
    writer.call('POST','/followups',dict(id='sim-followup',episode_id='sim-episode',due_at=iso(end+timedelta(days=1)),goal_description='Synthetic observation',protocol_reference='SYNTHETIC'))
    overdue=frontend.call('GET','/followups/sim-followup/status?'+urlencode({'as_of':iso(end+timedelta(days=2))}))
    review=writer.call('POST','/followups/reviews',dict(plan_id='sim-followup',measurement_ids=dataset.groups['recovery_vo2'],note='SYNTHETIC documented review',completed=True))
    completion=frontend.call('GET','/followups/sim-followup/status?'+urlencode({'as_of':review['reviewed_at']}))
    action=writer.call('POST','/action-requests',dict(episode_id='sim-episode',action='treatment',authorization_id='client-claims-authority'))
    operational=writer.call('POST','/evaluations',dict(rule_id='VIGILE-AER-001',**scope,as_of=iso(end),bindings={'vo2max_relative':dataset.groups['longitudinal_vo2'][-1]},mode='OPERATIONAL'))
    replay=writer.call('GET','/findings/'+gaps['id']+'/explanation')
    rag=reader.call('GET','/rag/findings/'+gaps['id'])
    if rag['result']!='INCONCLUSIVE' or any(k in rag for k in ('bundle','subject_id','mission_id','note_id','text')): raise AssertionError('RAG_SCOPE_LEAK')
    reader.call('POST','/evaluations',{'role':'clinician','authorized':True},expected=403)
    reader.call('GET','/measurements?'+query,expected=403)
    reader.call('GET','/rag/findings?'+urlencode({'subject_id':'other','mission_id':dataset.mission.id}),expected=403)
    reader.call('GET','/evidence/rules/VIGILE-ENV-002')
    discovered=reader.call('GET','/rag/findings?'+query)
    frontend.call('GET','/profiles?'+urlencode({'mission_id':dataset.mission.id}))
    frontend.call('GET','/profiles/'+dataset.profile.id)
    frontend.call('GET','/measurements?'+query)
    frontend.call('GET','/baselines?'+query); frontend.call('GET','/trends?'+query)
    frontend.call('GET','/episodes/sim-episode/pathway')
    reader.call('GET','/capabilities/coverage')
    resource=writer.call('POST','/resources/assessments',dict(mode='LOW_POWER',proposed_interval_seconds=120,
        required_interval_seconds=60,policy_reference='SYNTHETIC_NOT_FLIGHT_REQUIREMENT',measurement_ids=dataset.groups['co2_full'],as_of=iso(end)))
    audit=writer.call('GET','/audit/verify')
    assert audit['valid'] and not action['executed'] and operational['result']=='REQUIRES_VALIDATION'
    assert overdue['status']=='OVERDUE' and completion['status']=='COMPLETED_BY_HUMAN'
    assert multi['causality']=='NOT_INFERRED' and resource['result']=='POLICY_CONFLICT'
    assert trend['slope_per_day']<0 and recovery['slope_per_day']>0 and replay['verified']
    return {'synthetic':True,'clinical_validation':False,'measurement_count':len(dataset.measurements),
        'dataset_hash':digest(dataset.model_dump(mode='json')),'baseline_value':baseline['value'],
        'longitudinal_slope_per_day':trend['slope_per_day'],'postflight_slope_per_day':recovery['slope_per_day'],
        'findings':{'aerobic':aero['id'],'muscle':muscle['id'],'environment':co2['id'],'inconclusive':gaps['id']},
        'rule_results':[aero['result'],muscle['result'],co2['result']],
        'inconclusive_results':[{'result':f['result'],'reason':f['reason']} for f in [gaps,postflight,*faulty]],
        'quality_states':[a['state'] for a in quality['assessments']], 'multisystem':multi['causality'],
        'followup':completion['status'],'reader_results':len(discovered),'audit_valid':True,
        'replay_verified':True,'clinical_execution':'BLOCKED','resource_result':resource['result']}

def run(root,output=None,seed=42):
    root=Path(root); output=Path(output).resolve() if output else root/'engine/data/integration-runs'/secrets.token_hex(8)
    output.mkdir(parents=True,exist_ok=False); protect_directory(output)
    dataset=generate(seed); (output/'dataset.json').write_text(dataset.model_dump_json(indent=2),encoding='utf-8')
    writer_token=secrets.token_urlsafe(32); reader_token=secrets.token_urlsafe(32); front_token=secrets.token_urlsafe(32)
    key=lambda token:'sha256:'+hashlib.sha256(token.encode()).hexdigest()
    descriptors={key(writer_token):dict(id='demo-bootstrap',role='clinician',subject_ids=['*'],mission_ids=['*']),
        key(reader_token):dict(id='demo-rag',role='reader',subject_ids=[dataset.profile.id],mission_ids=[dataset.mission.id]),
        key(front_token):dict(id='demo-frontend',role='operator',subject_ids=[dataset.profile.id],mission_ids=[dataset.mission.id])}
    token_file=output/'server-tokens.json'; token_file.write_text(json.dumps(descriptors),encoding='utf-8')
    (output/'reader-token.txt').write_text(reader_token,encoding='utf-8'); (output/'frontend-token.txt').write_text(front_token,encoding='utf-8')
    with socket.socket() as sock: sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    env=os.environ.copy(); env.pop('VIGILE_TOKENS',None); env['VIGILE_TEST_NO_EXTERNAL_NETWORK']='1'
    started=time.perf_counter(); proc=None; writer=reader=frontend=None
    try:
        with (output/'server.log').open('w',encoding='utf-8') as log:
            proc=subprocess.Popen([sys.executable,'-m','vigile','serve','--port',str(port),'--integration-dir',str(output),'--managed-stdin'],
                cwd=root/'engine',env=env,stdin=subprocess.PIPE,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            writer=LocalClient('http://127.0.0.1:'+str(port),writer_token,True)
            for _ in range(150):
                try: writer.call('GET','/health'); break
                except (OSError,ValueError,httpx.TransportError):
                    if proc.poll() is not None: raise RuntimeError('SERVER_EXITED_SEE_LOCAL_LOG')
                    time.sleep(.1)
            else: raise RuntimeError('SERVER_START_TIMEOUT')
            startup=time.perf_counter()-started
            server_pid=json.loads((output/'server-process.json').read_text(encoding='utf-8'))['pid']
            writer.timings.clear()
            before=process_metrics(server_pid); wall=time.perf_counter()
            reader=LocalClient(writer.base_url,reader_token,True); frontend=LocalClient(writer.base_url,front_token,True)
            result=exercise(writer,reader,dataset,frontend)
            workload=time.perf_counter()-wall; after=process_metrics(server_pid)
            timings=writer.timings+reader.timings+frontend.timings; values=sorted(t['milliseconds'] for t in timings)
            cpu_delta=after.get('cpu_seconds',0)-before.get('cpu_seconds',0) if after.get('available') and before.get('available') else None
            live_storage=sum(f.stat().st_size for f in output.glob('vigile.sqlite3*'))
            result['performance']={'host_platform':platform.platform(),'python':platform.python_version(),'logical_cpus':os.cpu_count(),
                'startup_seconds':startup,'workload_seconds':workload,'server_pid_measured':server_pid,'requests':len(values),
                'request_latency_ms':{'median':statistics.median(values),'p95':values[max(0,__import__('math').ceil(.95*len(values))-1)],'max':max(values)},
                'server_counters_before':before,'server_counters_after':after,'workload_cpu_seconds':cpu_delta,
                'cpu_percent_one_core':None if cpu_delta is None else 100*cpu_delta/workload,'sqlite_live_bytes_including_wal':live_storage,
                'scope':'Single sequential synthetic workload. Includes audit and client overhead; not flight qualification or a load test.'}
            result['offline_test']='PASSED_WITH_PYTHON_EXTERNAL_SOCKET_GUARD_LOOPBACK_ALLOWED_NOT_OS_FIREWALL'
            result['output_directory']=str(output)
            (output/'api-examples.json').write_text(json.dumps(writer.transcript+reader.transcript+frontend.transcript,ensure_ascii=False,indent=2),encoding='utf-8')
            (output/'latencies.json').write_text(json.dumps(timings,indent=2),encoding='utf-8')
            (output/'openapi.json').write_text(json.dumps(writer.call('GET','/openapi.json'),indent=2),encoding='utf-8')
    finally:
        for client in (writer,reader,frontend):
            if client is not None: client.close()
        if proc is not None and proc.poll() is None:
            proc.stdin.close()
            try: proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.terminate(); proc.wait(timeout=10)
                raise RuntimeError('GRACEFUL_SHUTDOWN_FAILED')
        # Bootstrap write secret is never exported and is revoked, even if the demo fails.
        descriptors.pop(key(writer_token),None); token_file.write_text(json.dumps(descriptors),encoding='utf-8')
    store=Store(output/'vigile.sqlite3')
    try:
        assert store.verify()
        assert store.get('finding',result['findings']['inconclusive'])['result']=='INCONCLUSIVE'
        result['persisted_after_database_reopen']=True
        result['audit_checkpoint']=store.checkpoint()
    finally: store.close()
    result['performance']['sqlite_closed_bytes']=sum(f.stat().st_size for f in output.glob('vigile.sqlite3*'))
    (output/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
