from pathlib import Path
import json, os

def companyos_home():
    return Path(os.environ.get("COMPANYOS_HOME", str(Path.home()/'companyos')))

def load_dotenv(path=None):
    path=Path(path or companyos_home()/'.env')
    if not path.exists(): return
    for raw in path.read_text().splitlines():
        line=raw.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1)
        os.environ.setdefault(k.strip(),v.strip())

def load_config():
    load_dotenv()
    path=companyos_home()/'config'/'connectors.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text())

def env_value(name, default=None):
    if not name: return default
    return os.environ.get(name, default)
