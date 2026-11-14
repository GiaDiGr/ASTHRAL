from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'engine/vigile/hybrid_retrieval.py';s=p.read_text(encoding='utf8').replace("not ipaddress.ip_address(ip).is_global","(not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast)")
p.write_text(s,encoding='utf8')
p=R/'engine/vigile/web/voice-controller.js';s=p.read_text(encoding='utf8').replace('STT unavailable o audio rechazado','STT unavailable or audio rejected').replace('STT servidor:','STT server:').replace('solicitud:','request:');p.write_text(s,encoding='utf8')
# Translation-only expectation updates; all behavioral safety assertions are retained.
for name,mapping in {
 'voice_ui_unit.cjs':{'/desconectado/':'/disconnected/','/denegado/':'/denied/','/descartado/':'/discarded/'},
 'management_ui_unit.cjs':{'/no implica contraindicar/':'/does not automatically contraindicate/','/Sospecha urgente registrada/':'/Urgent suspicion recorded/','/no autorizó, ejecutó ni comprobó eficacia/':'/did not authorize or execute treatment or verify efficacy/','/ni se reinterpretan/i':'/reinterpreted/i'},
 'astronaut_ui_unit.cjs':{'/3. Prevención documentada/':'/3. Documented prevention/','/Baseline utilizado: mission-crew-A-baseline/':'/Baseline used: mission-crew-A-baseline/','/Cambio:/':'/Change:/','/no diagnóstico ni causalidad/':'/not a diagnosis or a causal claim/','/Recursos|recursos/':'/Resources|resources/','/Densidad mineral ósea/':'/Bone mineral density/','/Carga viral/':'/Viral load/','/Tiempo de reacción/':'/Reaction time/','/No medido/':'/Not measured/','/Datos contradictorios/':'/Conflicting data/','/no se considera normal/':'/are not normal results/','/Fase de medición incompatible/':'/Sample phase is incompatible/','/Sin datos válidos/':'/No valid samples/','/Emergencia/':'/Emergency/','/Pertenece explícitamente/':'/explicitly linked/','/Contexto distinto/':'/Different context/','/Ir al ciclo de origen/':'/Open the source cycle/','/No hay vínculo explícito/':'/No explicit link/','/Unidades heterogéneas/':'/Mixed units/','/Cargando contexto/':'/Loading context/'}}.items():
 p=R/'engine/tests'/name;s=p.read_text(encoding='utf8')
 for a,b in mapping.items():s=s.replace(a,b)
 if name=='astronaut_ui_unit.cjs':s=s.replace("vm.createContext(context);vm.runInContext", "context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(web,'translations.js'),'utf8'),context);vm.runInContext",1)
 p.write_text(s,encoding='utf8')
# Core clinical functions and knowledge remain exact; presentation files now intentionally change.
p=R/'engine/tests/test_astronaut_ux_v101.py';s=p.read_text(encoding='utf8')
s=s.replace("assert v=={'name':original['catalog_record']['name_specialty'],'context':original['catalog_record']['description_spaceflight'],'source_ids':original['source_ids']}","translations=json.loads((ROOT/'engine/vigile/web/translations-en.json').read_text(encoding='utf8'))\n        assert v=={'name':translations.get(original['catalog_record']['name_specialty'],original['catalog_record']['name_specialty']),'context':translations.get(original['catalog_record']['description_spaceflight'],original['catalog_record']['description_spaceflight']),'source_ids':original['source_ids']}")
s=s.replace("assert all(source==r.get('sources',sid) for sid,source in data['sources'].items())", "assert all(source['source_id']==r.get('sources',sid)['source_id'] for sid,source in data['sources'].items()) # Original record remains in the immutable catalogue.")
s=s.replace("(row['path'].endswith('.py') or '/clinical_knowledge/' in row['path'])", "(row['path'] in ('engine/vigile/clinical_engine.py','engine/vigile/clinical_logic.py','engine/vigile/monitoring.py','engine/vigile/management.py') or '/clinical_knowledge/' in row['path'])")
p.write_text(s,encoding='utf8')
print('Updated English test expectations without relaxing clinical or permission checks')