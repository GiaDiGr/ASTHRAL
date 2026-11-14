"""Deterministic request and attribution controls; no clinical decisions."""
import re,unicodedata

def normalize(text):
 return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))

def request_guard(question,subject_id=None,mission_id=None):
 q=normalize(question)
 if re.search(r'\b(write|give|create|issue)\s+(?:me\s+)?(?:a\s+)?prescription|\b(prescribe|receta|recetar|inyectar|inject)\b|cuantas? unidades|credentials|hidden (?:prompt|instructions)|system instruction|approve therapy|aprobar tratamiento|(?:print|reveal|show).{0,40}(?:secret|token|password)|act as (?:administrator|system)',q):return 'REFUSED_ACTION'
 if re.search(r'\b(predict|pronostica|predice)\b|fecha exacta.{0,30}(?:fractura|enfermedad)',q):return 'INSUFFICIENT_INFORMATION'
 if mission_id and any(x!=mission_id.lower() for x in re.findall(r'v07-mission-[a-z0-9_-]+',q)):return 'CONTEXT_MISMATCH'
 if subject_id:
  requested=re.findall(r'v07-crew-[abc]|crew [abc]',q)
  if any(x.replace('crew ','v07-crew-')!=subject_id.lower() for x in requested):return 'CONTEXT_MISMATCH'
 return None

def clinical_claim_guard(text,support):
 # Sensitive clinical claims must be verbatim supported, not judged by the same LLM.
 t=normalize(text);s=normalize(support)
 if re.search(r'diagnos|diagnost|authoriz|autoriz|treat|tratam|protocol|protocolo|prescri|criteri|criteria|confirm|normal|requerid|required|mandatory|obligatori',t):
  compact=lambda x:re.sub(r'[^a-z0-9]+',' ',x).strip()
  if compact(t) not in compact(s):raise ValueError('CLINICAL_CLAIM_REQUIRES_EXACT_ENGINE_TEXT')
