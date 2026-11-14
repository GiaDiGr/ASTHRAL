from pathlib import Path
import re,json
R=Path(__file__).resolve().parents[2]
for file in ['app.js','management.js','voice-controller.js']:
 s=(R/'engine/vigile/web'/file).read_text(encoding='utf8');out=[]
 for m in re.finditer(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`",s):
  t=m.group()[1:-1]
  if re.search(r'[áéíóúñ¿¡]|\b(?:de |del |para |Sin |sin |datos|Datos|Ver |No |el |la |Un |una |por |que |voz|VIGILE|Protocolo|Medici|Ciclo)',t) and len(t)<1000:out.append(t)
 (R/'work/asthral'/('strings-'+file+'.json')).write_text(json.dumps(list(dict.fromkeys(out)),ensure_ascii=False,indent=2),encoding='utf8')
 print(file,len(set(out)))