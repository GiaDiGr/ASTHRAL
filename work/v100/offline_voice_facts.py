from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'engine/vigile/longitudinal_assistant.py';s=p.read_text(encoding='utf8')
start=s.index("    if getattr(inference,'structured_explanations',False):\n        from .structured_facts")
mid=s.index("        if not facts:return result",start)
block=s[start:mid];s=s[:start]+"    if getattr(inference,'structured_explanations',False):\n        from .structured_facts import explain\n"+s[mid:]
anchor="    if result['mode']=='CRITICAL':return result";assert anchor in s;s=s.replace(anchor,block+anchor)
p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/voice.py';s=p.read_text(encoding='utf8')
s=s.replace("    return {k:v for k,v in os.environ.items() if not k.upper().startswith('VIGILE_') and not any(x in k.upper() for x in ('TOKEN','PASSWORD','SECRET','API_KEY'))}", "    allowed={'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','PSMODULEPATH','COMSPEC','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','PROCESSOR_ARCHITECTURE','PROCESSOR_IDENTIFIER','NUMBER_OF_PROCESSORS','HOMEDRIVE','HOMEPATH','PATHEXT'}\n    return {k:v for k,v in os.environ.items() if k.upper() in allowed}")
s=s.replace("            entries=[]", "            if not row['files']:raise ValueError('EMPTY_MODEL_MANIFEST')\n            entries=[]")
p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/voice_api.py';s=p.read_text(encoding='utf8')
s=s.replace("    if result['status'] in ('REFUSED_ACTION','CONTEXT_MISMATCH'):", "    if result['status'] in ('REFUSED_ACTION','CONTEXT_MISMATCH'):")
p.write_text(s,encoding='utf8')