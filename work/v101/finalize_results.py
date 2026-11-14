from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];D=R/'docs/v101'
load=lambda p:json.loads((D/p).read_text(encoding='utf8'))
freeze=load('CODE_FREEZE.json');assert all(hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in freeze['files'])
final=ET.parse(D/'final-tests.xml').getroot()[0];specific=ET.parse(D/'hardening-tests.xml').getroot()[0]
assert final.attrib['tests']=='687' and final.attrib['failures']==final.attrib['errors']==final.attrib['skipped']=='0'
assert specific.attrib['tests']=='54' and specific.attrib['failures']=='0'
r2=load('r2-replay-verification.json');print('R2 report keys',list(r2))
p=load('preservation.json');assert p['clinical_semantic_hash']==p['r2_semantic_hash']
report=load('demo-report.json');assert freeze['implementation_hash']==report['scenarios'][0]['evaluation']['implementation_hash']
results={'version':'1.0.1','date':'2026-10-31','status':'TECHNICALLY_INTEGRABLE_SYNTHETIC_RESEARCH_SUPPORT','clinical_execution':'BLOCKED','clinical_validation':False,'operational_or_flight_validation':False,'implementation_hash':freeze['implementation_hash'],'knowledge_hash':p['clinical_knowledge_hash'],'code_archive_sha256':freeze['sha256'],'source_freeze_verified_after_tests':True,'full_suite':{k:final.attrib[k] for k in ('tests','failures','errors','skipped','time','timestamp')},'warnings':[{'category':'StarletteDeprecationWarning','message':'httpx with starlette.testclient deprecated; existing dependency retained, no installation or dependency change'}],'new_targeted_tests':{k:specific.attrib[k] for k in ('tests','failures','errors','skipped','time','timestamp')},'simulated_DOM_scenarios':6,'original_synthetic_cases_compared':30,'semantic_hash_equal_to_R2':p['clinical_semantic_hash'],'clinical_knowledge_files_unchanged':len(p['clinical_knowledge_files']),'unchanged_clinical_functions':p['diagnostic_functions'],'archived_r2_replays':len(r2['replays']),'archived_r2_all_matches':all(x['matches'] for x in r2['replays']),'demo':{'scenarios':len(report['scenarios']),'inventory_versions':4,'clinical_replays':len(report['clinical_replays']),'monitoring_replays':len(report['monitoring_replays']),'all_match':all(x['matches'] for x in report['clinical_replays']+report['monitoring_replays']),'human_records':len(report['management_records']),'audit_valid':report['audit_valid'],'verified_backup_and_restored_replays':True,'no_real_treatment_administered':True},'live_HTTP':load('http-integration.json'),'backend_reader_GETs_verified':4,'backend_reader_write_status':403,'powershell_external_reader_example_verified':True,'browser_visual_QA':'PENDING_CUA_KERNEL_ASSET_INITIALIZATION_ERROR','physical_voice_QA':'PENDING_FROM_R2_NOT_RETESTED','LLM_new_generation_test':'NOT_PERFORMED_NO_NEW_LLM_FEATURES_OR_RESERVED_BANK_REUSE','new_dependencies':[],'security_limits':['SQLITE_WAL_BACKUPS_NOT_ENCRYPTED','SAME_USER_PROCESSES_NOT_ISOLATED','STORAGE_CONTROL_CAN_REWRITE_HASH_CHAIN','NO_VERIFIED_MISSION_MEDICAL_AUTHORITY'],'clinical_pending_review':'CLINICAL_REVIEW.md','development_failures':'Earlier development XML retained separately; fixture token length/lineage and DOM text assertion corrected; final run is final-tests.xml'}
(D/'RESULTS.json').write_text(json.dumps(results,indent=2),encoding='utf8')
(D/'COVERAGE.md').write_text('''# Cobertura de apoyo terapéutico v1.0.1

Se distinguen representación, comprobación por software y validación clínica. Esta tabla no acredita eficacia ni uso operacional. Las siete rutas, diferencial y umbrales previos se conservan; las 44 condiciones del catálogo no adquieren por ello terapéutica computacional.

| Ruta | Representación nueva | Comprobación de software | Pendiente clínico |
|---|---|---|---|
| Diabetes | Revisión/protocolo previo, pruebas y recursos separados de tratamiento | Suite clínica previa y comparación de casos R2 | Indicación/intervención humana; no régimen nuevo |
| DKA | Insulinoterapia documental, restricción de K específica; revisión de capacidad IV; snapshot recursos | K faltante, fronteras previas, recursos disponibles/vencidos/desconocidos, diagnóstico invariante, replays | Discrepancia <3.5/<=3.5; pautas/condiciones textuales no ejecutadas; revisión primaria terapéutica |
| Hipoglucemia | Contexto declarado de deglución válido/ausente/contradictorio, revisión original | Calidad/tiempo/futuro y UNKNOWN conservados | No régimen oral/glucagón añadido sin fuente aprobada |
| OH | Revisión previa y aplicabilidad gravitatoria preservada | Microgravedad/limitaciones y suite original | Retorno/contramedidas no constituyen pauta individual |
| POTS | Revisión previa y limitaciones de descondicionamiento | Microgravedad, aplicabilidad y suite original | No extrapolación farmacológica a vuelo |
| AKI | Reglas previas sólo documentales, recursos/autoridad separados | Suite previa, casos R2 y hashes | Fuente local sólo definición KDIGO Section 2; localizar manejo primario |
| Anafilaxia | Sospecha urgente separada de criterios, epinefrina documental, soporte con mapeo pendiente | SUSPECTED+EMERGENCY sin recursos; no confirmación ni autorización | Trigger/indicación, sitio, precauciones y tratamiento requieren aprobación humana |
| Diferencial | Sin modificaciones de reglas/ordenamiento/pruebas diagnósticas | Igualdad exacta de 30 casos y suite completa | No validación clínica independiente |

Inventario/followup/contramedidas añaden representación y verificaciones de software; no activan terapias, confirmación médica, pronóstico ni eficacia. Todas las etapas terapéuticas con juicio clínico siguen pendientes de autoridad y revisión. Sin cambios de tratamiento SANS, predicción de cáncer o dosis por microgravedad.

G01/G02/G03/G04/G07 implementados como apoyo documental y software sintético; G05 bloqueado; G06 incertidumbres explícitas con revisión terapéutica pendiente; G08 integración documental limitada. No se declara cierre clínico de G06 ni exhaustividad del catálogo de precauciones.

Resultados: 687 pruebas totales (54 nuevas), cero fallos/errores/omisiones; seis escenarios DOM simulados; cinco escenarios de demo; 11+1 replays nuevos y 76 archivados R2. Los seis escenarios DOM forman parte de una prueba pytest, no seis pruebas extra sumables al total. Inspección visual y voz física pendientes. RESULTS.json y XML conservan evidencia exacta.
''',encoding='utf8')
with (D/'README.md').open('a',encoding='utf8') as f:f.write('''
## Resultado de cierre y siguiente revisión

Suite final: **687 aprobadas, cero fallos/errores/omisiones**, 464.77 segundos según salida pytest (tiempo JUnit en RESULTS.json). Una advertencia de deprecación Starlette/httpx, sin cambiar dependencias. Las 54 pruebas nuevas incluyen una prueba que ejecuta seis escenarios DOM simulados. 30 casos originales idénticos a R2; 76 replays archivados correctos; demo nueva con 11 replays clínicos y uno de monitorización correctos, también después de restaurar respaldo verificado. Inventario, manejo y seguimiento accesibles por reader; escritura reader rechazada con 403.

Entrega técnica apta para integración de investigación con datos sintéticos, ejecución terapéutica siempre bloqueada y consumidores adaptados al contrato aditivo. Pendientes: revisión clínica de CLINICAL_REVIEW.md, inspección visual real, prueba física de voz, aislamiento y cifrado de almacenamiento/política operacional. No validación clínica independiente, operacional ni de vuelo.

Detalle: IMPLEMENTATION.md, INTEGRATION_CONTRACTS.md, COVERAGE.md y EXAMPLES.md. Resultados reales completos en examples.json/demo-report.json; esquema exacto en openapi.json; archivo de código recuperable sin bases, credenciales o pesos en candidate-code-v101.zip y CODE_FREEZE.json. Base privada sólo en engine/data/mission-v101-final; respaldo verificado privado en work/v101/final-db-backup. Copiar código no redistribuye ni aprovisiona credenciales/modelos.

Próximo trabajo priorizado: (1) revisión humana de discrepancias terapéuticas y fuentes/localizadores, (2) QA visual y voz física, (3) aislamiento/cifrado/política de autoridad de misión antes de considerar datos reales, (4) integración de consumidores sobre OpenAPI y pruebas de contrato. Mantener bloqueos hasta aprobación y validación adecuadas.
''')
print(json.dumps({'final_tests':final.attrib['tests'],'new_tests':specific.attrib['tests'],'archived_R2_replays':len(r2['replays']),'all_archived_match':results['archived_r2_all_matches'],'post_test_source_freeze_verified':True}))