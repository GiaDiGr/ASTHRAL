from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'engine/tests/test_asthral_hybrid.py';s=p.read_text(encoding='utf8').replace("model=NoModel();model.mode='FULL'", "model=NoModel();model.mode='FULL';model.set_mode=lambda mode:setattr(model,'mode',mode)");p.write_text(s,encoding='utf8')
p=R/'engine/tests/test_astronaut_ux_v101.py';s=p.read_text(encoding='utf8').replace('capture_output=True,text=True,timeout=30','capture_output=True,text=True,encoding=\'utf8\',timeout=30');p.write_text(s,encoding='utf8')
import subprocess
node=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
fixture=Path.home()/'AppData/Local/Temp/pytest-of-Gianni/pytest-15/test_astronaut_actual_assets_s0/synthetic-frames.json'
p=subprocess.run([str(node),str(R/'engine/tests/astronaut_ui_unit.cjs'),str(fixture)],capture_output=True,text=True,encoding='utf8');(R/'work/asthral/dom-diagnostic.txt').write_text(p.stdout+p.stderr,encoding='utf8');print((p.stdout+p.stderr)[:1600]);print('NODE_EXIT',p.returncode)