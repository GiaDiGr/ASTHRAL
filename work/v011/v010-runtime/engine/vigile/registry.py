"""Read-only import of supplied evidence; original records remain unchanged."""
from pathlib import Path
import json, hashlib, re, csv, io
from copy import deepcopy
from .store import digest

CATALOGS = {
 "conditions": ("03_CATALOGO/condiciones_con_rutas_y_cobertura.json", "condition_id"),
 "sources": ("07_EVIDENCIAS/fuentes.json", "source_id"),
 "extractions": ("07_EVIDENCIAS/extracciones.json", "evidence_id"),
 "algorithms": ("04_ALGORITMOS/algoritmos.json", "algorithm_id"),
 "interactions": ("06_MULTISISTEMA/interacciones.json", "interaction_id"),
 "datasets": ("08_DATASETS/datasets.json", "dataset_id"),
 "synthetic_cases": ("09_TESTS/casos_sinteticos.json", "test_id"),
 "reconstructed": ("02_REGLAS_ORIGINALES_15/inventario_10_reconstruidas.json", "rule_id"),
 "rules": ("02_REGLAS_ORIGINALES_15/REGLAS_15_ORIGINALES.json", "rule_id"),
 "sensors": ("05_SENSORES/sensores_biomarcadores.json", "variable"),
}
COUNTS=dict(zip(CATALOGS,[44,38,24,12,12,12,20,10,15,28]))
CONDITION_MAP={"AER":["C001"],"MUS":["C002"],"BONE":["C003"],"NUT":["C023"],"RAD":["C032"]}
CONDITION_MAP.update({"ENV-001":["C026"],"ENV-002":["C027"],"ENV-003":["C026","C030"],"ENV-004":["C031"]})

class Registry:
    def __init__(self, root):
        self.root=Path(root)
        self.catalogs={}
        self.hashes={}
        self.issues=[]
        manifest=json.loads((self.root/'MANIFIESTO_SHA256.json').read_text(encoding='utf-8-sig'))
        for item in manifest:
            p=(self.root/item['path']).resolve()
            if not p.is_relative_to(self.root.resolve()):
                raise ValueError('Manifest path escapes corpus')
            if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
                raise ValueError('Original corpus integrity failure: '+item['path'])
        for kind,(file,key) in CATALOGS.items():
            raw=(self.root/file).read_bytes()
            records=json.loads(raw)
            indexed={r[key]:r for r in records}
            if len(indexed)!=len(records) or len(records)!=COUNTS[kind]:
                raise ValueError('Duplicate IDs or unexpected count: '+kind)
            self.catalogs[kind]=indexed
            self.hashes[file]=hashlib.sha256(raw).hexdigest()
        for c in self.catalogs['conditions'].values():
            if len(c['coverage_states'])!=11:
                raise ValueError('Coverage stages missing')
            for sid in c['source_ids']:
                if sid not in self.catalogs['sources']:
                    raise ValueError('Unresolved source: '+sid)
        for e in self.catalogs['extractions'].values():
            if e['source_id'] not in self.catalogs['sources']:
                raise ValueError('Broken extraction reference')
        for rule in self.catalogs['rules'].values():
            individual=json.loads((self.root/'02_REGLAS_ORIGINALES_15/individual'/f"{rule['rule_id']}.json").read_bytes())
            if individual!=rule:
                raise ValueError('Individual/combined rule mismatch')
        rows=list(csv.DictReader((self.root/'03_CATALOGO/matriz_cobertura_44x11.csv').read_text(encoding='utf-8-sig').splitlines()))
        stage_keys=['P','M','Q','D','A','DD','T','I','R','F','G']
        for row in rows:
            condition=self.catalogs['conditions'][row['condition_id']]
            if list(condition['coverage_states'].values()) != [row[k] for k in stage_keys]:
                raise ValueError('Coverage matrix mismatch')
            single=json.loads((self.root/'03_CATALOGO/condiciones_individuales'/f"{row['condition_id']}.json").read_bytes())
            if single != condition:
                raise ValueError('Condition duplicate mismatch')
        self.issues=[
          {'id':'EVID-001','status':'REQUIRES_VALIDATION','detail':'S27 is OSD-198 but C015/C027 narrative cites it for CO2; do not resolve as CO2 evidence.'},
          {'id':'EVID-002','status':'REQUIRES_VALIDATION','detail':'Original rule source namespaces differ from S01-S38. Explicit mapping required; raw IDs preserved.'},
          {'id':'EVID-003','status':'REQUIRES_VALIDATION','detail':'Citation tokens from Deep Research are not independently resolvable offline evidence.'},
          {'id':'PROV-001','status':'RECORDED','detail':'Consolidated report says original 15 unavailable; current package includes 15 recovered from a later report, not the lost ZIP.'},
          {'id':'COV-001','status':'REQUIRES_VALIDATION','detail':'ES in supplied coverage is documentary support, never clinical executable authorization.'},
        ]
        self.fingerprint=digest(self.hashes)

    def list(self, kind):
        return deepcopy(list(self.catalogs[kind].values()))

    def get(self, kind, identifier):
        return deepcopy(self.catalogs[kind][identifier])

    def rule(self, identifier):
        return self.get('rules',identifier)

    def conditions_for(self, identifier):
        suffix=identifier.removeprefix('VIGILE-')
        return CONDITION_MAP.get(suffix, CONDITION_MAP.get(suffix.split('-')[0], []))

    def rule_status(self):
        return [{'rule_id':r['rule_id'],'simulation':'IMPLEMENTED','operational':'REQUIRES_VALIDATION',
                 'clinical_execution':'BLOCKED','rule_hash':digest(r),'source_locators':r['source_locators'],
                 'condition_ids':self.conditions_for(r['rule_id'])} for r in self.list('rules')]+[
                 {'rule_id':'R-ORTHO-001','simulation':'REQUIRES_MISSION_AUTHORIZATION','operational':'REQUIRES_VALIDATION','clinical_execution':'BLOCKED'}]

    def import_to(self, store):
        identifier=self.fingerprint
        try:
            return store.get('corpus', identifier)
        except KeyError:
            return store.put('corpus',identifier,{'fingerprint':identifier,'catalogs':self.catalogs,
                 'file_hashes':self.hashes,'issues':self.issues,'operational_activation':'BLOCKED'})
