from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[2]
p=R/'docs/v101/final-tests.xml';shutil.copy2(p,R/'docs/v101/full-development-02-tests.xml')
p=R/'engine/vigile/clinical_engine.py';s=p.read_text(encoding='utf8');needle="    def evaluate(self,request,actor,parent_id=None,identifier=None):\n";assert s.count(needle)==1;s=s.replace(needle,needle+"        with self.store.transaction():\n            return self._evaluate_frozen(request,actor,parent_id,identifier)\n    def _evaluate_frozen(self,request,actor,parent_id=None,identifier=None):\n");p.write_text(s,encoding='utf8')
p=R/'engine/vigile/management.py';s=p.read_text(encoding='utf8');s=s.replace("    return {name:resource_check(snapshot,name)['status']=='RESOURCE_AVAILABLE' for name in names}","    checked={name:resource_check(snapshot,name)['status'] for name in names}\n    return {name:state=='RESOURCE_AVAILABLE' for name,state in checked.items() if state!='RESOURCE_UNVERIFIED'}")
s=s.replace("r['diagnostic_status'] in ('NOT_APPLICABLE','CRITERIA_NOT_MET')", "r['diagnostic_status']=='NOT_APPLICABLE'")
s=s.replace("for m in ev.get('management',{}).values() for i in m['interventions']", "for i in ev.get('management',{}).get(ep['condition_id'],{}).get('interventions',[])")
s=s.replace("if x.get('protocol_id')==pid and (condition!='DKA' or insulin)","if x.get('protocol_id')==pid and (condition!='DKA' or insulin) and (condition!='ANAPHYLAXIS' or title=='EPINEPHRINE_IM')")
p.write_text(s,encoding='utf8')
p=R/'engine/vigile/web/management.js';s=p.read_text(encoding='utf8');needle="   technical(item,'Precauciones documentales";s=s.replace(needle,"   item.append(el('p','Catálogo de contraindicaciones y precauciones incompleto: ausencia de regla no acredita seguridad; revisión humana pendiente.'));\n"+needle);p.write_text(s,encoding='utf8')