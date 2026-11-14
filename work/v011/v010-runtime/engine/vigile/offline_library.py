"""Hash-pinned, bounded offline excerpts; documentary text never grants authority."""
from pathlib import Path
import json,hashlib,re

class OfflineLibrary:
    def __init__(self,path):
        self.path=Path(path) if path else None
        self._manifest_cache=None;self._manifest_digest=None
    def search(self,question,limit=2):
        from .local_assistant import tokens
        if self.path is None:return [],['DOCUMENT_LIBRARY_NOT_CONFIGURED']
        try:
            if self.path.stat().st_size>4_000_000:raise ValueError('LIBRARY_TOO_LARGE')
            raw=self.path.read_bytes();fingerprint=hashlib.sha256(raw).hexdigest()
            if fingerprint==self._manifest_digest:manifest=self._manifest_cache
            else:
                manifest=json.loads(raw);self._manifest_cache=manifest;self._manifest_digest=fingerprint
            rows=manifest['blocks']
            if manifest.get('schema_version')==2:
                from .knowledge_v08 import search
                return search(manifest,question,limit)
            if hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()!=manifest['sha256']:raise ValueError('LIBRARY_INTEGRITY_FAILED')
            query=tokens(question);ranked=sorted(rows,key=lambda b:-len(query&tokens(b['text'])))
            found=[b for b in ranked if len(query&tokens(b['text']))>=2][:limit]
            return found,([] if found else ['NO_MATCHING_DOCUMENT_EXCERPT'])
        except MemoryError:return [],['DOCUMENT_LIBRARY_RESOURCE_LIMIT']
        except (OSError,ValueError,KeyError,TypeError):return [],['DOCUMENT_LIBRARY_MISSING_OR_INVALID']

def build(root,output):
    root=Path(root);source=root/'docs/clinical/deep-research-report-2026-10-16.md'
    raw=source.read_bytes();text=raw.decode('utf-8');sha=hashlib.sha256(raw).hexdigest();blocks=[]
    # Only this reviewed local research report is admitted; no directory crawl.
    for match in re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*',text):
        paragraph=match.group().strip()
        if len(paragraph)<100:continue
        for offset in range(0,len(paragraph),1500):
            part=paragraph[offset:offset+1500]
            blocks.append({'id':'D'+str(len(blocks)+1),'kind':'DOCUMENT','text':part,'reference':{'document':'deep-research-report-2026-10-16.md','sha256':sha,'line':text[:match.start()].count('\n')+1,'character_offset':offset,'authority':'RESEARCH_REPORT_NOT_PATIENT_RESULT'}})
    manifest={'schema_version':1,'blocks':blocks,'sha256':hashlib.sha256(json.dumps(blocks,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
    Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'blocks':len(blocks),'source_sha256':sha,'manifest_sha256':manifest['sha256']}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[2],args.output)))
