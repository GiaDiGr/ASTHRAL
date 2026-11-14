"""Protect a newly prepared synthetic demo; never print backend credentials."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.local_protection import PREFIX,protect_secret,restrict_directory,verified_backup,anchor_database,verify_anchor
p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--backup',type=Path,required=True);p.add_argument('--anchor',type=Path,required=True);p.add_argument('--key',type=Path,required=True);a=p.parse_args();folder=a.folder.resolve();acl=restrict_directory(folder)
for name in ('reader-token.txt','portal-access.txt','server-tokens.json'):
 file=folder/name;raw=file.read_text(encoding='utf8').strip()
 if raw.startswith(PREFIX):continue
 temporary=folder/(name+'.dpapi-tmp');protect_secret(raw,temporary);temporary.replace(file)
config=json.loads((folder/'portal-config.json').read_text(encoding='utf8'));config.update(session_idle_seconds=900,session_absolute_seconds=28800);(folder/'portal-config.json').write_text(json.dumps(config,indent=2),encoding='utf8')
backup=verified_backup(folder/'vigile.sqlite3',a.backup);anchor_database(folder/'vigile.sqlite3',a.anchor,a.key);check=verify_anchor(folder/'vigile.sqlite3',a.anchor,a.key)
print(json.dumps({'acl':acl,'backup':backup,'anchor':check,'database_encrypted':False},indent=2))
