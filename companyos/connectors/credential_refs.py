import json, os
from pathlib import Path

class CredentialReferenceStore:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"connector_credential_refs.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return {}
        try:return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:return {}

    def register_env(self, connector, env_vars):
        d=self.load()
        d[connector]={"env_vars":list(env_vars or [])}
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        return self.status(connector)

    def status(self, connector):
        refs=self.load().get(connector,{}).get("env_vars",[])
        return {
            "connector":connector,
            "configured":all(bool(os.environ.get(x)) for x in refs) if refs else True,
            "env_vars":refs
        }
