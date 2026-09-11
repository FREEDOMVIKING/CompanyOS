import os

class CredentialChecker:
    def check(self, required_env):
        required=list(required_env or [])
        missing=[x for x in required if not os.environ.get(x)]
        return {"configured":not missing,"missing":missing,"required":required}
