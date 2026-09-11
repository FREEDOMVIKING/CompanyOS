import argparse,json,shutil
from pathlib import Path
from .engine import APIBackboneEngine
def init():
 h=Path.home()/'companyos';cfg=h/'config'/'api_profiles.json';ex=h/'config'/'api_profiles.example.json';cfg.parent.mkdir(parents=True,exist_ok=True)
 if not cfg.exists():shutil.copyfile(ex,cfg) if ex.exists() else cfg.write_text('{"profiles":{}}');print('Created',cfg)
 else:print('Config already exists:',cfg)
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['init','health','demo']);a=p.parse_args()
 if a.command=='init':init();return
 e=APIBackboneEngine();print(json.dumps(e.health() if a.command=='health' else e.demo(),indent=2))
if __name__=='__main__':main()
