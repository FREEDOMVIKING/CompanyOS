#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "${HOME}/companyos"
ENV_FILE="${HOME}/.companyos_launch_env"
BACKUP=".companyos_runtime/cloudflare_install_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP" companyos/connectors scripts tests/generated
echo "===== COMPANYOS CLOUDFLARE PRIMARY HOSTING INSTALL ====="
[ -f "$ENV_FILE" ] && { set -a; . "$ENV_FILE"; set +a; }
: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN missing}"
: "${CLOUDFLARE_ACCOUNT_ID:?CLOUDFLARE_ACCOUNT_ID missing}"
cp companyos/website_deployer/engine.py "$BACKUP/engine.py" 2>/dev/null || true

cat > companyos/connectors/cloudflare_hosting.py <<'PY'
from __future__ import annotations
import json, mimetypes, os, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path
API="https://api.cloudflare.com/client/v4"

class CloudflareError(RuntimeError): pass

class CloudflareHosting:
    def __init__(self, token=None, account_id=None):
        self.token=(token or os.getenv("CLOUDFLARE_API_TOKEN","")).strip()
        self.account_id=(account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID","")).strip()

    @property
    def configured(self): return bool(self.token and self.account_id)

    def _request(self, method, path, body=None, headers=None):
        if not self.configured: raise CloudflareError("Cloudflare credentials are not configured")
        h={"Authorization":f"Bearer {self.token}","Accept":"application/json"}
        if headers: h.update(headers)
        data=body
        if isinstance(body,(dict,list)):
            data=json.dumps(body).encode()
            h["Content-Type"]="application/json"
        req=urllib.request.Request(API+path,data=data,headers=h,method=method)
        try:
            with urllib.request.urlopen(req,timeout=60) as r: raw=r.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            raw=e.read().decode("utf-8","replace")
            raise CloudflareError(f"Cloudflare HTTP {e.code}: {raw[:1000]}")
        obj=json.loads(raw or "{}")
        if not obj.get("success",False):
            raise CloudflareError("Cloudflare API error: "+json.dumps(obj.get("errors",[])))
        return obj

    def verify(self): return self._request("GET","/user/tokens/verify").get("result",{})
    def list_projects(self):
        return self._request("GET",f"/accounts/{self.account_id}/pages/projects").get("result",[])
    def project(self,name):
        n=urllib.parse.quote(name,safe="")
        return self._request("GET",f"/accounts/{self.account_id}/pages/projects/{n}").get("result",{})

    def ensure_project(self,name,production_branch="main"):
        try: return self.project(name)
        except CloudflareError as e:
            if "HTTP 404" not in str(e): raise
        return self._request("POST",f"/accounts/{self.account_id}/pages/projects",
                             {"name":name,"production_branch":production_branch}).get("result",{})

    @staticmethod
    def _multipart(fields,files):
        boundary="----CompanyOS"+uuid.uuid4().hex
        c=[]
        for name,value in fields.items():
            c += [f"--{boundary}\r\n".encode(),
                  f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                  str(value).encode(),b"\r\n"]
        for field,filename,content in files:
            ctype=mimetypes.guess_type(filename)[0] or "application/octet-stream"
            c += [f"--{boundary}\r\n".encode(),
                  f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode(),
                  f"Content-Type: {ctype}\r\n\r\n".encode(),content,b"\r\n"]
        c += [f"--{boundary}--\r\n".encode()]
        return b"".join(c),f"multipart/form-data; boundary={boundary}"

    def deploy_directory(self,project_name,directory,production_branch="main"):
        root=Path(directory).expanduser().resolve()
        if not root.is_dir(): raise CloudflareError(f"Site directory does not exist: {root}")
        self.ensure_project(project_name,production_branch)
        files=[("file",p.relative_to(root).as_posix(),p.read_bytes())
               for p in sorted(root.rglob("*")) if p.is_file()]
        if not files: raise CloudflareError("Site directory contains no files")
        body,ctype=self._multipart({"branch":production_branch},files)
        n=urllib.parse.quote(project_name,safe="")
        r=self._request("POST",f"/accounts/{self.account_id}/pages/projects/{n}/deployments",
                        body,{"Content-Type":ctype}).get("result",{})
        return {"provider":"cloudflare","project":project_name,"deployment_id":r.get("id"),
                "url":r.get("url"),"environment":r.get("environment"),
                "aliases":r.get("aliases") or [],"status":"submitted"}

    def health(self):
        if not self.configured:
            return {"provider":"cloudflare","configured":False,"dry_run":True,
                    "healthy":False,"reason":"missing_credentials"}
        try:
            token=self.verify(); projects=self.list_projects()
            return {"provider":"cloudflare","configured":True,"dry_run":False,
                    "healthy":token.get("status")=="active",
                    "token_status":token.get("status"),"project_count":len(projects)}
        except Exception as e:
            return {"provider":"cloudflare","configured":True,"dry_run":True,
                    "healthy":False,"reason":str(e)}
PY

cat > companyos/connectors/hosting_router.py <<'PY'
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
PY

cat > scripts/companyos_cloudflarectl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
env=Path.home()/".companyos_launch_env"
if env.exists():
    for raw in env.read_text().splitlines():
        raw=raw.strip()
        if raw.startswith("export ") and "=" in raw:
            k,v=raw[7:].split("=",1); os.environ.setdefault(k.strip(),v.strip().strip("'").strip('"'))
from companyos.connectors.cloudflare_hosting import CloudflareHosting
from companyos.connectors.hosting_router import HostingRouter
p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
s.add_parser("health"); s.add_parser("projects")
d=s.add_parser("deploy"); d.add_argument("directory"); d.add_argument("--project",default="companyos-commissioning"); d.add_argument("--branch",default="main")
a=p.parse_args()
if a.cmd=="health": r=HostingRouter().health()
elif a.cmd=="projects": r=CloudflareHosting().list_projects()
else: r=HostingRouter().deploy_directory(a.project,a.directory,a.branch)
print(json.dumps(r,indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_cloudflarectl

cat > tests/generated/test_cloudflare_hosting.py <<'PY'
from companyos.connectors.cloudflare_hosting import CloudflareHosting
from companyos.connectors.hosting_router import HostingRouter
def test_unconfigured_is_dry(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN",raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID",raising=False)
    h=CloudflareHosting().health()
    assert h["configured"] is False and h["dry_run"] is True
def test_router_prefers_cloudflare(monkeypatch):
    monkeypatch.setattr(CloudflareHosting,"health",lambda self:{"provider":"cloudflare","configured":True,"dry_run":False,"healthy":True})
    h=HostingRouter().health()
    assert h["provider"]=="cloudflare" and h["healthy"] is True
def test_directory_validation(tmp_path):
    c=CloudflareHosting("x","y")
    try: c.deploy_directory("x",tmp_path/"missing")
    except Exception as e: assert "does not exist" in str(e)
    else: raise AssertionError("expected validation error")
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/website_deployer/engine.py"); s=p.read_text()
needle='''        connectors=read_json(self.home/"companyos_runtime"/"connectors"/"health.json",{}).get("connectors",{})
        hosting=connectors.get("hosting",{})
        publish_ready=bool(hosting.get("configured")) and not bool(hosting.get("dry_run",True))
'''
replacement='''        # Provider-neutral live hosting; Cloudflare is primary.
        try:
            from companyos.connectors.hosting_router import HostingRouter
            hosting=HostingRouter().health()
        except Exception:
            connectors=read_json(self.home/"companyos_runtime"/"connectors"/"health.json",{}).get("connectors",{})
            hosting=connectors.get("hosting",{})
        publish_ready=bool(hosting.get("configured")) and not bool(hosting.get("dry_run",True))
'''
if needle in s:
    p.write_text(s.replace(needle,replacement)); print("PATCHED website_deployer/engine.py")
elif "HostingRouter" in s: print("website_deployer already Cloudflare-aware")
else: raise SystemExit("SAFE ABORT: expected WebsiteDeployer block not found")
PY

echo "===== COMPILE ====="
python -m py_compile companyos/connectors/cloudflare_hosting.py companyos/connectors/hosting_router.py companyos/website_deployer/engine.py
echo "===== TESTS ====="
python -m pytest -q tests/generated/test_cloudflare_hosting.py
echo "===== CLOUDFLARE HEALTH ====="
python scripts/companyos_cloudflarectl health
echo "===== PROJECTS ====="
python scripts/companyos_cloudflarectl projects

SITE=".companyos_runtime/cloudflare_commissioning_site"; mkdir -p "$SITE"
cat > "$SITE/index.html" <<'HTML'
<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CompanyOS</title><h1>CompanyOS</h1><p>Cloudflare production hosting connector commissioned successfully.</p>
HTML
echo "===== REAL REVERSIBLE PAGES DEPLOYMENT ====="
python scripts/companyos_cloudflarectl deploy "$SITE" --project companyos-commissioning --branch main | tee .companyos_runtime/cloudflare_commissioning_result.json
echo "===== STATUS ====="
git status --short
echo "COMPANYOS_CLOUDFLARE_PRIMARY_HOSTING=PASS"
echo "BACKUP=$BACKUP"
