from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'engine/tests/test_management_v101.py';s=p.read_text(encoding='utf8');s=s.replace("mapping={'writer':'researcher','reader':", "mapping={'writer'*8:'researcher','reader'*8:").replace("'operator':{'id':'o'", "'operator'*8:{'id':'o'").replace("'outsider':{'id':'x'", "'outsider'*8:{'id':'x'");s=s.replace("'Bearer '+token","'Bearer '+token*8").replace("'Bearer writer'","'Bearer '+('writer'*8)").replace("'Bearer reader'","'Bearer '+('reader'*8)").replace("'Bearer outsider'","'Bearer '+('outsider'*8)").replace("'Bearer operator'","'Bearer '+('operator'*8)")
s=s.replace(" later=clinical.evaluate(req(data={**DATA,'potassium_mmol_l':4},resource_policy='MISSION_INVENTORY',as_of=T+timedelta(hours=3)),'researcher') if False else None", " later=clinical.evaluate(req(data={**DATA,'potassium_mmol_l':4},resource_policy='MISSION_INVENTORY').model_copy(update={'as_of':T+timedelta(hours=3)}),'researcher')\n assert later['results']['DKA']['protocol_status']=='BLOCKED_RESOURCE'\n assert view(later)['resource_snapshot']['inventory_version']==2")
s=s.replace("{'id':'bad','effective_at':T,'updated_at':T}","{'id':'bad','version':3,'supersedes':'inventory-2','effective_at':T,'updated_at':T}")
s+='''\n\ndef test_monitoring_freezes_inventory_and_replays(clinical):
 from vigile.monitoring import MonitoringService
 from vigile.monitoring_models import MonitoringRequest
 populate(clinical)
 request=MonitoringRequest(id='inventory-monitoring',subject_id='clinical-crew',mission_id='clinical-earth',resource_policy='MISSION_INVENTORY',as_of=T,history_start=T-timedelta(days=1),clinical_window_start=T-timedelta(hours=2),clinical_context_id='synthetic-context',policy_reference='SYNTHETIC_ONLY',population='NONPREGNANT_ADULT',age_years=30,observations=[observation(k,v) for k,v in DATA.items()])
 service=MonitoringService(clinical.engine);out=service.run(request,'researcher')
 assert out['clinical_evaluations']['DKA']['management']['DKA']['resource_snapshot']['inventory_version']==1
 assert service.replay(out['id'])['matches']
\n\ndef test_cross_astronaut_management_record_rejected(clinical):
 out,entry=record_setup(clinical)
 clinical.engine.register('profile',AstronautProfile(id='second',mission_id='clinical-earth',synthetic=True),'researcher')
 clinical.engine.open_episode(EpisodeRequest(id='other-episode',subject_id='second',mission_id='clinical-earth',condition_id='DKA'),'researcher')
 with pytest.raises(ValueError,match='SCOPE'):append_management_record(clinical.engine,entry.model_copy(update={'episode_id':'other-episode'}),'clinician')
''';p.write_text(s,encoding='utf8')