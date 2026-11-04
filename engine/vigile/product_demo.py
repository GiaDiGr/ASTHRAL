"""VIGILE product preparation reuses the unchanged 54-day mission scenario.
Runtime setup never downloads models. Fresh directory and fresh DPAPI credentials.
"""
from pathlib import Path
import argparse,json
from .mission_demo import prepare,serve

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','serve']);p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=int,default=42);p.add_argument('--model-config',type=Path);a=p.parse_args()
 if a.command=='serve':return serve(a.output)
 result=prepare(a.output,a.seed,a.model_config)
 configpath=a.output.resolve()/'portal-config.json';config=json.loads(configpath.read_text(encoding='utf8'))
 config.update(voice_enabled=True,structured_explanations=True)
 configpath.write_text(json.dumps(config,indent=2),encoding='utf8')
 print(json.dumps({k:result[k] for k in ('cycles','request_hash','semantic_hash','implementation_hash','total_seconds','database_bytes')},indent=2))
if __name__=='__main__':main()