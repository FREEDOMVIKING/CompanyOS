import os
class CredentialReadiness:
    def check(self, env_vars):
        env_vars=list(env_vars or [])
        missing=[x for x in env_vars if not os.environ.get(x)]
        return {"ready":not missing,"missing":missing,"required":env_vars}
