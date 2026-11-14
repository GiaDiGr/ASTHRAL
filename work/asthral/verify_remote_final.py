from pathlib import Path
import sys,json,ssl,httpx,subprocess,hashlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import read_secret
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();expected={r['path'] for r in json.loads((R/'docs/asthral/publication-safety.json').read_text())['manifest']}
with httpx.Client(verify=ssl.create_default_context(),trust_env=False,timeout=20,headers={'Authorization':'Bearer '+read_secret(R/'work/asthral/github-token.dpapi'),'Accept':'application/vnd.github+json'}) as c:
 repo=c.get('https://api.github.com/repos/GiaDiGr/ASTHRAL');repo.raise_for_status();repo=repo.json();assert repo['private'] and repo['owner']['login']=='GiaDiGr'
 branches={}
 for branch in ['main','feature/asthral-hybrid']:
  response=c.get('https://api.github.com/repos/GiaDiGr/ASTHRAL/branches/'+branch);response.raise_for_status();branches[branch]=response.json()['commit']['sha'];assert branches[branch]==sha
 tree=c.get('https://api.github.com/repos/GiaDiGr/ASTHRAL/git/trees/'+sha,params={'recursive':'1'});tree.raise_for_status();tree=tree.json();assert not tree.get('truncated');paths={row['path'] for row in tree['tree'] if row['type']=='blob'};assert paths==expected
 for forbidden in ['engine/data/','engine/local_ai/','work/','engine/.venv/']:assert not any(p.startswith(forbidden) for p in paths)
 required={'README.md','CONTRIBUTING.md','engine/vigile/hybrid_retrieval.py','engine/vigile/web/index.html','engine/tools/demo_asthral.py','docs/asthral/verification-summary.json'};assert required<=paths
report={'account':'GiaDiGr','repo_url':repo['html_url'],'visibility':'PRIVATE','default_branch':repo['default_branch'],'branches':branches,'commit_sha':sha,'remote_tree_files':len(paths),'remote_tree_matches_exact_reviewed_manifest':True,'source_pushed':True,'secrets_databases_models_and_private_configs_excluded':True,'no_force_push':True,'collaborator_invitations_sent':False,'project_license_added':False}
(R/'docs/asthral/github-publication.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
assert subprocess.check_output(['git','status','--porcelain'],cwd=R)==b''
subprocess.run(['git','bundle','create',str(R/'work/asthral/asthral-1.1.0-final.bundle'),'--all'],cwd=R,check=True,capture_output=True)
print('Working tree clean; local recovery bundle created')