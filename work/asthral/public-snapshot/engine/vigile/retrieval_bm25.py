"""Local BM25 ranking over unchanged, provenance-verified excerpts.
No embeddings, remote calls, synthesized scientific text or new medical rules.
"""
from collections import Counter
import re,math,unicodedata
GROUPS=[('baseline','baselines','basal','basales'),('select','selected','selection','elige','elegir','seleccion','seleccionar'),('validate','validated','validation','valida','validar','validacion'),('repeat','repeated','repeating','repetir','repetidas','repetidos','repeticion'),('notification','notifications','notificaciones','notificacion','alert','alerts','alerta','alertas'),('overlap','overlapping','solapamiento','solapamientos','solapados'),('radiation','radiacion','dosimetry','dosimetria'),('limitation','limitations','limitaciones','limitacion','limit','limits'),('freshness','fresh','frescura','antiguedad','stale','desactualizado'),('window','windows','ventana','ventanas','temporales','temporal'),('device','devices','dispositivo','dispositivos','sensor','sensors','sensores'),('muscle','muscular','musculars','musculo','musculos','strength','fuerza'),('bone','osea','oseo','hueso','huesos'),('density','densidad'),('hypoglycemia','hipoglucemia'),('diabetes','diabetic','diabetica','diabetico'),('ketoacidosis','cetoacidosis','dka'),('potassium','potasio'),('glucose','glucosa'),('level','levels','nivel','niveles'),('boundary','boundaries','threshold','thresholds','limite','limites','umbral','umbrales'),('1','one','uno'),('2','two','dos'),('availability','available','disponibilidad','disponible'),('monitoring','monitorizacion','vigilancia'),('microgravity','microgravedad'),('oxygen','oxigeno'),('negation','negacion')]
ALIASES={w:row[0] for row in GROUPS for w in row}
STOP=set('how are is the and what which can be as to of for during my during a an these those se el la los las de del como que cual cuales un una y por para durante mi sus su'.split())
def tokens(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))
    return [ALIASES.get(t,t) for t in re.findall(r'[a-z]+|\d+(?:[.,]\d+)?',text) if t not in STOP and (len(t)>1 or t.isdigit())]

def rank(rows,question,text_cache):
    q=Counter(tokens(question));bags=[];headings=[]
    for row in rows:
        ref=row['reference'];text=text_cache[ref['document']][1];prefix=text[:ref['char_start']]
        hs=re.findall(r'^#{1,6}\s+(.+)$',prefix,re.M)[-2:]
        heading=' '.join(hs);headings.append(set(tokens(heading)))
        bags.append(Counter(tokens(row['text'])))
    n=len(rows);avg=sum(sum(b.values()) for b in bags)/max(n,1)
    df={t:sum(t in b for b in bags) for t in q};scores=[]
    for i,(row,bag) in enumerate(zip(rows,bags)):
        size=sum(bag.values());score=0
        for t in q:
            f=bag[t];idf=math.log(1+(n-df[t]+.5)/(df[t]+.5))
            score+=idf*(f*2.2)/(f+1.2*(.25+.75*size/max(avg,1))) if f else 0
            if t in headings[i]:score+=.3*idf
        authority=row['reference']['authority']
        if authority=='PRIMARY_SOURCE_SHORT_EXCERPT' and set(q)&{'hypoglycemia','level','boundary'}:score*=1.3
        if authority.startswith('IMPLEMENTATION') and set(q)&{'select','validate','repeat','freshness','window'}:score*=1.1
        scores.append(score)
    # Keep source diversity, but do not force unrelated documents into a short list.
    order=sorted(range(n),key=lambda i:(-scores[i],rows[i]['id']))
    return [(rows[i],scores[i]) for i in order if scores[i]>0]