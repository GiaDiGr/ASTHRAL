from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'engine/tools/setup_asthral.py';s=p.read_text(encoding='utf8');s=s.replace(" print(json.dumps", " legacy=ROOT/'engine/local_ai/library-v080.json'\n if not legacy.exists():legacy.write_bytes((ROOT/'engine/local_ai/library-asthral.json').read_bytes())\n print(json.dumps");p.write_text(s,encoding='utf8')
# The owner retains all historical manifests; the compatibility alias is created only on clean setups.
print('Clean setup can regenerate the legacy filename without overwriting an existing pinned library')