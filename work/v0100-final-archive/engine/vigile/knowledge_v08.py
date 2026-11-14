"""Bounded, provenance-checked sparse retrieval. No remote calls at query time."""
from pathlib import Path
import hashlib,json,re,math,unicodedata
from functools import lru_cache

ROOT=Path(__file__).resolve().parents[2]
SOURCES=[
 ('docs/clinical/deep-research-report-2026-10-16.md','CLINICAL_RESEARCH_SYNTHESIS','2026-10-16'),
 ('01_INFORMES/REPORTE_CONSOLIDADO_COMPLETO.md','SPACE_RESEARCH_SYNTHESIS','PINNED_CORPUS'),
 ('docs/v07/README.md','IMPLEMENTATION_DOCUMENTATION_NOT_GUIDELINE','0.7.0'),
 ('docs/v07/CONTRACTS.md','IMPLEMENTATION_CONTRACT','0.7.0'),
 ('engine/vigile/clinical_knowledge/v07-extension.json','IMPLEMENTED_CRITERION_NOT_ORIGINAL_ARTICLE','2026.1'),
 ('docs/v08/sources/ADA2026-short-excerpt.txt','PRIMARY_SOURCE_SHORT_EXCERPT','2026-table-6.4')]
INJECTION=re.compile(r'ignore (?:all |previous |the )?(?:instructions|rules)|ignora.{0,30}(?:reglas|instrucciones)|system prompt|reveal.{0,30}(?:secret|token)|<script|\[INST\]|role\s*:\s*system',re.I)
GROUPS={
 'coverage':'coverage cobertura intervals intervalos accumulated acumulada acumulado',
 'limitation':'limitation limitations limites limitacion limitaciones',
 'baseline':'baseline basal referencia baselines', 'trend':'trend trends tendencia tendencias longitudinal evolution evolucion cambio cambios changed change difference diferencia compare compara',
 'radiation':'radiation radiacion radiologica radiological dosis dose dosimetry dosimetria',
 'sleep':'sleep sueno dormir fatigue fatiga comportamiento behavioral', 'immune':'immune inmunologico inmunologica inmune viral immunity',
 'muscle':'muscle muscular musculoesqueletico musculoesqueletica strength fuerza bone osea oseo',
 'cardiovascular':'cardiovascular aerobico aerobica aerobic vo2 vo2max retention retencion hemodynamic hemodinamica',
 'quality':'quality calidad sensor sensores sensors invalid invalidos invalidas invalido invalida valida desconocido unknown stale desactualizado contradictorio contradictory',
 'hypoglycemia':'hypoglycemia hipoglucemia glucose glucosa capillary capilar',
 'missing':'missing faltan falta faltante faltantes ausente ausentes insufficient insuficiente insuficientes',
 'alert':'alert alerta alertas event evento eventos priority prioridad urgency urgencia',
 'microgravity':'microgravity microgravedad gravity gravedad', 'evidence':'evidence evidencia fuente fuentes source sources referencia reference',
 'protocol':'protocol protocolo treatment tratamiento safety seguridad authorization autorizacion',
}
ALIASES={word:key for key,words in GROUPS.items() for word in words.split()}
STOP=set('que como por para los las del una uno con sin the and how what which why has have during from this that been was are is my mi durante respecto estado fisiologico physiology physiological mission mision me you your de en el la los las'.split())
def terms(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))
    return {ALIASES.get(w,w) for w in re.findall(r'[a-z0-9]{3,}',text) if w not in STOP}
@lru_cache(maxsize=1024)
def document_terms(text):
    return frozenset(terms(text))

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(rows):return json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()

def build(root,output):
    root=Path(root);rows=[];missing=[];documents=[]
    for name,authority,version in SOURCES:
        p=root/name
        if not p.exists():missing.append(name);continue
        raw=p.read_bytes();text=raw.decode('utf-8-sig');fingerprint=sha(raw)
        documents.append({'document':name,'sha256':fingerprint,'authority':authority,'version':version})
        for match in re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*',text):
            for start in range(match.start(),match.end(),1100):
                end=min(start+1100,match.end());excerpt=text[start:end]
                if len(excerpt.strip())<25:continue
                reference={'document':name,'sha256':fingerprint,'version':version,'authority':authority,'char_start':start,'char_end':end,'line':text[:start].count('\n')+1}
                if authority=='PRIMARY_SOURCE_SHORT_EXCERPT':reference.update(source_id='SRC-ADA-HYPO-2026',url='https://doi.org/10.2337/dc26-S006',verified_date='2026-10-21',coverage='SHORT_EXCERPT_ONLY_NOT_FULL_TEXT')
                rows.append({'id':'D-'+sha(canonical(reference))[:20],'kind':'DOCUMENT','text':excerpt,'reference':reference})
    manifest={'schema_version':2,'retrieval_version':'SPARSE-BILINGUAL-1','documents':documents,'missing_documents':missing,'blocks':rows,'sha256':sha(canonical(rows))}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return {k:v for k,v in manifest.items() if k!='blocks'}|{'blocks':len(rows)}

def search(manifest,question,limit,root=ROOT):
    rows=manifest['blocks'];issues=[];verified=[];cache={}
    if sha(canonical(rows))!=manifest['sha256']:raise ValueError('LIBRARY_INTEGRITY_FAILED')
    seen=set()
    for b in rows:
        r=b['reference'];name=r['document']
        if name not in cache:
            p=(root/name).resolve()
            if not p.is_relative_to(root.resolve()) or name not in {s[0] for s in SOURCES}:raise ValueError('DOCUMENT_PATH_NOT_ALLOWED')
            raw=p.read_bytes()
            if len(raw)>2_000_000:raise ValueError('DOCUMENT_TOO_LARGE')
            cache[name]=(sha(raw),raw.decode('utf-8-sig'))
        h,text=cache[name]
        if h!=r['sha256'] or text[r['char_start']:r['char_end']]!=b['text'] or b['id'] in seen:raise ValueError('EXCERPT_PROVENANCE_FAILED')
        if b['kind']!='DOCUMENT' or r['authority']!=next(a for n,a,v in SOURCES if n==name):raise ValueError('DOCUMENT_AUTHORITY_INVALID')
        if r['version']!=next(v for n,a,v in SOURCES if n==name):raise ValueError('DOCUMENT_VERSION_INVALID')
        if not isinstance(r['char_start'],int) or not isinstance(r['char_end'],int) or not 0<=r['char_start']<r['char_end']<=len(text):raise ValueError('DOCUMENT_OFFSETS_INVALID')
        if r['line']!=text[:r['char_start']].count('\n')+1 or b['id']!='D-'+sha(canonical(r))[:20]:raise ValueError('DOCUMENT_REFERENCE_INVALID')
        expected={'document':name,'sha256':h,'version':next(v for n,a,v in SOURCES if n==name),'authority':next(a for n,a,v in SOURCES if n==name),'char_start':r['char_start'],'char_end':r['char_end'],'line':r['line']}
        if expected['authority']=='PRIMARY_SOURCE_SHORT_EXCERPT':expected.update(source_id='SRC-ADA-HYPO-2026',url='https://doi.org/10.2337/dc26-S006',verified_date='2026-10-21',coverage='SHORT_EXCERPT_ONLY_NOT_FULL_TEXT')
        if r!=expected:raise ValueError('DOCUMENT_METADATA_INVALID')
        seen.add(b['id'])
        if INJECTION.search(b['text']):issues.append('DOCUMENT_INSTRUCTION_QUARANTINED:'+b['id']);continue
        verified.append(b)
    q=terms(question);bags=[document_terms(b['text']) for b in verified];n=len(bags)
    frequency={t:sum(t in bag for bag in bags) for t in q}
    def score(index):
        bag=bags[index];return sum(math.log(1+(n+1)/(frequency[t]+1)) for t in q&bag)/(1+len(bag)/150)
    ranked=sorted(range(n),key=lambda i:(-score(i),verified[i]['id']))
    found=[];per_document={}
    for i in ranked:
        name=verified[i]['reference']['document']
        if score(i)<=0 or per_document.get(name,0)>=2:continue
        found.append({**verified[i],'retrieval_score':round(score(i),6)})
        per_document[name]=per_document.get(name,0)+1
        if len(found)>=limit:break
    if not found:issues.append('NO_MATCHING_DOCUMENT_EXCERPT')
    issues+=['SOURCE_CONTENT_UNAVAILABLE:'+name for name in manifest.get('missing_documents',[])]
    return found,issues

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();print(json.dumps(build(ROOT,args.output),indent=2))
