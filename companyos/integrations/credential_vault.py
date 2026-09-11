import json, os
from pathlib import Path

class CredentialVault:
    """Stores references to env var names, never plaintext secret values."""
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"credential_refs.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def register_env_ref(self, integration, env_var):
        d=self.load()
        d[integration]={"env_var":env_var}
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        return {"integration":integration,"env_var":env_var,"configured":bool(os.environ.get(env_var))}

    def load(self):
        if not self.path.exists(): return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:return {}

    def status(self, integration):
        ref=self.load().get(integration,{})
        env_var=ref.get("env_var")
        return {"integration":integration,"env_var":env_var,"configured":bool(env_var and os.environ.get(env_var))}
