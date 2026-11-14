from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'engine/vigile/web'
for name in ['app.js','management.js','voice-controller.js']:
 p=W/name;s=p.read_text(encoding='utf8')
 fixes={"'Urgencia'":"'Urgency'","'Dato'":"'Data'","'Consultando evidencia autorizada…'":"'Retrieving authorized evidence…'",'?.value||"es"':'?.value||"en"',"'State completo, hallazgos y transiciones'":"'Full state, findings, and transitions'","' · ciclo: '":"' · cycle: '","'ciclo '":"'cycle '","' a '":"' at '","'Ver '":"'View '","'sin muestra'":"'no sample'","'desconocida'":"'unknown'"}
 for a,b in fixes.items():s=s.replace(a,b)
 p.write_text(s,encoding='utf8')
print('Finished remaining English interface labels and language defaults')