import os

class CredentialReadiness:
    def evaluate(self, registry):
        result={}
        for name,cfg in (registry or {}).items():
            missing=[k for k in cfg.get("required_env",[]) if not os.getenv(k)]
            result[name]={
                "configured": not missing,
                "missing_env": missing
            }
        return result
