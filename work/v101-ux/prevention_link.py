from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'engine/vigile/web/management.js';s=p.read_text(encoding='utf8')
s=s.replace("['3. Evaluación y manejo','clinical'],['4. Seguimiento','followup']","['3. Prevención documentada','monitoring'],['4. Evaluación y manejo','clinical'],['5. Seguimiento','followup']")
s=s.replace("if(text.startsWith('2.'))$('findings').parentElement.open=true;","if(text.startsWith('2.'))$('findings').parentElement.open=true;if(text.startsWith('3.'))$('space-monitoring').parentElement.open=true;")
p.write_text(s,encoding='utf8')
p=R/'engine/tests/astronaut_ui_unit.cjs';s=p.read_text(encoding='utf8');s=s.replace("assert.match(h.text('journey-context'),/mission-crew-A-cycle-35/);","assert.match(h.text('journey-context'),/mission-crew-A-cycle-35/);assert.match(h.text('journey-links'),/3. Prevención documentada/);")
p.write_text(s,encoding='utf8');print('Added direct prevention navigation; final targeted test will verify final assets')