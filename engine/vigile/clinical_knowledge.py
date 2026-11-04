"""Pinned local evidence. Source verification labels are not perpetual validity."""
from pathlib import Path
import json,hashlib
from .store import digest

class ClinicalKnowledge:
    def __init__(self,path=None):
        self.path=Path(path or Path(__file__).with_name('clinical_knowledge'))
        self.manifest=json.loads((self.path/'manifest.json').read_text(encoding='utf-8'))
        self.documents={}
        for name,expected in self.manifest['files'].items():
            raw=(self.path/name).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('CLINICAL_KNOWLEDGE_HASH_MISMATCH')
            self.documents[name.removesuffix('.json')]=json.loads(raw)
        extension_path=self.path/'v07-extension.json'
        if path is None and not extension_path.exists():raise ValueError('REQUIRED_CLINICAL_EXTENSION_MISSING')
        if extension_path.exists():
            raw=extension_path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!='b258ff2d79ab79355f65826466c9fc3e7a52380b749ec18ef2eb4700759e4fd8': raise ValueError('CLINICAL_EXTENSION_HASH_MISMATCH')
            extension=json.loads(raw)
            self.documents['v07_extension']=extension
            for doc,key in [('diagnostic_criteria','criteria'),('sources_verified','sources'),('treatment_protocols','protocols'),('diagnostic_tests','tests')]:
                self.documents[doc][key].extend(extension[key])
            self.manifest={**self.manifest,'version':'0.7.0','extensions':{'v07-extension.json':'b258ff2d79ab79355f65826466c9fc3e7a52380b749ec18ef2eb4700759e4fd8'}}
        self.sources={s['source_id']:s for s in self.documents['sources_verified']['sources']}
        self.criteria={s['condition_id']:s for s in self.documents['diagnostic_criteria']['criteria']}
        self.protocols={s['protocol_id']:s for s in self.documents['treatment_protocols']['protocols']}
        self.tests={s['test_id']:s for s in self.documents['diagnostic_tests']['tests']}
        self.presentations={s['presentation_id']:s for s in self.documents['differential_rules']['presentations']}
        self.hash=digest(self.documents)
        for criterion in self.criteria.values():
            if any(s not in self.sources for s in criterion['source_ids']): raise ValueError('MISSING_CLINICAL_SOURCE')
    def source_status(self,identifier):
        s=self.sources[identifier]
        if s.get('type')=='DRAFT_GUIDELINE' or 'DRAFT' in s.get('verification',''): return 'DRAFT_NOT_FOR_PRODUCTION'
        if s.get('verification') not in ('VERIFIED','VERIFIED_CURRENT_DOCUMENT'): return 'UNVERIFIED_OR_NONCURRENT'
        return 'PINNED_VERIFIED_AT_REPORT_DATE_NOT_CONTINUOUSLY_VERIFIED'
    def usable(self,identifier): return self.source_status(identifier).startswith('PINNED_')
