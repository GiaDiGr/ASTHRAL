from pathlib import Path
p=Path(__file__).resolve().parents[2]/'engine/vigile/web/app.js';s=p.read_text(encoding='utf8')
s=s.replace("const label=x=>", "const displayNumber=x=>Number.isFinite(x)?new Intl.NumberFormat('es-PE',{maximumFractionDigits:3}).format(x):String(x??'Ausente');\nconst label=x=>",1)
s=s.replace(":indicator.value,'value')",":displayNumber(indicator.value),'value')")
s=s.replace("+indicator.baseline_comparison.absolute_change+' '","+displayNumber(indicator.baseline_comparison.absolute_change)+' '")
s += "\nObject.assign(names,{'mission-crew-A':'Astronauta sintético A','mission-crew-B':'Astronauta sintético B','mission-v011':'Misión integrada v0.11','physiology.strength':'Fuerza medida','sleep.duration':'Duración del sueño','environment.ppo2':'Presión parcial de O₂ ambiental'});\n"
p.write_text(s,encoding='utf8')
