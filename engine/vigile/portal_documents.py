"""Exact verified fragment lookup; never a filesystem proxy."""
import re,json
from fastapi import HTTPException
from .knowledge_v08 import search

def exact_fragment(library,identifier):
 if not re.fullmatch(r'D-[a-f0-9]{20}',identifier):raise HTTPException(404,'UNKNOWN_FRAGMENT')
 try:
  if library.path is None or library.path.stat().st_size>4_000_000:raise HTTPException(503,'LIBRARY_UNAVAILABLE')
  manifest=json.loads(library.path.read_text(encoding='utf8'))
  if manifest.get('schema_version')!=2:raise ValueError('UNSUPPORTED_LIBRARY')
  _,issues=search(manifest,'__verify_without_retrieval__',1)
  if 'DOCUMENT_INSTRUCTION_QUARANTINED:'+identifier in issues:raise HTTPException(503,'FRAGMENT_QUARANTINED')
  block=next((b for b in manifest['blocks'] if b['id']==identifier),None)
  if not block:raise HTTPException(404,'UNKNOWN_FRAGMENT')
  return {**block,'relevance':'NOT_INDEPENDENTLY_VALIDATED','authority_is_not_patient_state':True}
 except (OSError,ValueError,KeyError,TypeError):raise HTTPException(503,'LIBRARY_UNAVAILABLE')
