import argparse,json,shutil
from pathlib import Path
from .config import companyos_home
from .engine import ConnectorEngine

def init_config():
    home=companyos_home()
    cfg=home/'config'/'connectors.json'
    example=home/'config'/'connectors.example.json'
    cfg.parent.mkdir(parents=True,exist_ok=True)
    if not cfg.exists():
        if example.exists(): shutil.copyfile(example,cfg)
        else: cfg.write_text('{}')
        print(f'Created {cfg}')
    else:
        print(f'Config already exists: {cfg}')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['init-config','health','demo'])
    a=p.parse_args()
    if a.command=='init-config':
        init_config();return
    e=ConnectorEngine()
    if a.command=='health':
        print(json.dumps(e.health(),indent=2))
    elif a.command=='demo':
        print(json.dumps(e.demo_workflow(),indent=2))

if __name__=='__main__':
    main()
