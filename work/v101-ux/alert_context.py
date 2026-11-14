from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'engine/vigile/web/management.js'
with p.open('a',encoding='utf8') as f:f.write('''
// Preserve priority while naming its time contexts; never declare an old alert resolved.
const renderAlertBeforeAstronaut=renderPersistentAlert;renderPersistentAlert=function(){renderAlertBeforeAstronaut();const banner=$('persistent-clinical-alert');if(banner.hidden||!dashboard)return;const cycle=guideCycle();banner.textContent+=' Contextos visibles: '+(cycle?'ciclo '+cycle.id+' a '+cycle.as_of:'sin ciclo verificable')+(selected?'; evaluación '+selected.id+' a '+selected.as_of:'')+'. No se infiere resolución ni simultaneidad entre fechas distintas.';};
''')
print('Priority preserved with explicit dates and context IDs')