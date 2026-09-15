import os
from .cloudflare_hosting import CloudflareHosting
class HostingRouter:
    def __init__(self): self.cloudflare=CloudflareHosting()
    def health(self):
        cf=self.cloudflare.health()
        if cf.get("healthy"):
            return {"configured":True,"dry_run":False,"healthy":True,
                    "provider":"cloudflare","cloudflare":cf}
        return {"configured":False,"dry_run":True,"healthy":False,"provider":None,
                "cloudflare":cf,"optional_vercel_configured":bool(os.getenv("VERCEL_TOKEN","").strip())}
    def deploy_directory(self,project_name,directory,production_branch="main"):
        h=self.health()
        if h.get("provider")=="cloudflare":
            return self.cloudflare.deploy_directory(project_name,directory,production_branch)
        raise RuntimeError("No healthy production hosting provider is available")
