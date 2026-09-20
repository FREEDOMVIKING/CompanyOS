#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
ENV_FILE="$HOME/.companyos_launch_env"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.companyos_backups/cloudflare_hosting_$STAMP"

echo "CompanyOS Cloudflare Full Hosting Bundle"
cd "$ROOT"
mkdir -p "$BACKUP" "$ROOT/.companyos_runtime/deployments"

[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found"; exit 1; }
set +u
source "$ENV_FILE"
set -u
[ -n "${CLOUDFLARE_API_TOKEN:-}" ] || { echo "ERROR: CLOUDFLARE_API_TOKEN missing"; exit 1; }
[ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ] || { echo "ERROR: CLOUDFLARE_ACCOUNT_ID missing"; exit 1; }

for f in companyos/connectors_live/registry.py config/connectors.json; do
  [ -f "$f" ] && { mkdir -p "$BACKUP/$(dirname "$f")"; cp -a "$f" "$BACKUP/$f"; }
done

if ! command -v npx >/dev/null 2>&1; then
  pkg install -y nodejs-lts
fi

cat > companyos/connectors_live/cloudflare_adapter.py <<'PY'
from __future__ import annotations
import json, os, re, shutil, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request
from .base import BaseConnector, ConnectorError
from .config import env_value

class CloudflareHostingConnector(BaseConnector):
    name="hosting"
    provider="cloudflare"
    API_BASE="https://api.cloudflare.com/client/v4"

    def is_configured(self):
        return self.enabled and bool(env_value("CLOUDFLARE_API_TOKEN")) and bool(env_value("CLOUDFLARE_ACCOUNT_ID"))

    def health(self):
        h=super().health()
        h.update({"provider":"cloudflare","pages_ready":self.is_configured(),"workers_ready":self.is_configured(),
                  "token_set":bool(env_value("CLOUDFLARE_API_TOKEN")),
                  "account_id_set":bool(env_value("CLOUDFLARE_ACCOUNT_ID"))})
        return h

    def _slug(self,p):
        n=p.get("project_name") or p.get("company_name") or p.get("company_id") or p.get("name") or "companyos-site"
        n=re.sub(r"[^a-z0-9-]+","-",str(n).lower().strip())
        return (re.sub(r"-{2,}","-",n).strip("-") or "companyos-site")[:58]

    def _api(self,method,path,payload=None,allow_404=False):
        token=env_value("CLOUDFLARE_API_TOKEN")
        data=None if payload is None else json.dumps(payload).encode()
        req=request.Request(self.API_BASE+path,data=data,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},method=method)
        try:
            with request.urlopen(req,timeout=self.timeout) as r:
                raw=r.read().decode("utf-8","replace")
                obj=json.loads(raw) if raw else {}
        except error.HTTPError as e:
            body=e.read().decode("utf-8","replace")
            if allow_404 and e.code==404: return None
            raise ConnectorError(f"Cloudflare HTTP {e.code}: {body[:1200]}") from e
        if isinstance(obj,dict) and obj.get("success") is False:
            raise ConnectorError("Cloudflare API rejected request: "+json.dumps(obj.get("errors",[]))[:1200])
        return obj

    def _ensure_project(self,project,branch="main"):
        account=env_value("CLOUDFLARE_ACCOUNT_ID")
        path=f"/accounts/{parse.quote(account)}/pages/projects/{parse.quote(project)}"
        if self._api("GET",path,allow_404=True) is not None:
            return False
        self._api("POST",f"/accounts/{parse.quote(account)}/pages/projects",{"name":project,"production_branch":branch or "main"})
        return True

    def _root(self,p):
        files=p.get("files")
        if isinstance(files,dict) and files:
            tmp=Path(tempfile.mkdtemp(prefix="companyos_cf_"))
            for name,content in files.items():
                rel=str(name).lstrip("/").replace(chr(92),"/")
                if not rel or ".." in Path(rel).parts:
                    shutil.rmtree(tmp,ignore_errors=True); raise ConnectorError(f"unsafe deploy path: {name}")
                dst=tmp/rel; dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_bytes(content if isinstance(content,bytes) else str(content).encode())
            return tmp,True
        raw=p.get("website_path") or p.get("site_path") or p.get("artifact_path") or p.get("path") or p.get("artifact")
        if not raw: raise ConnectorError("deploy_production requires website_path/site_path/path or files")
        root=Path(str(raw)).expanduser()
        if not root.is_absolute():
            a=Path.cwd()/root; b=Path.home()/"companyos"/root
            root=a if a.exists() else b
        if not root.exists(): raise ConnectorError(f"website path not found: {root}")
        if root.is_file():
            tmp=Path(tempfile.mkdtemp(prefix="companyos_cf_file_")); shutil.copy2(root,tmp/root.name); return tmp,True
        return root,False

    def _wrangler(self,args,cwd=None):
        env=os.environ.copy()
        env["CLOUDFLARE_API_TOKEN"]=env_value("CLOUDFLARE_API_TOKEN")
        env["CLOUDFLARE_ACCOUNT_ID"]=env_value("CLOUDFLARE_ACCOUNT_ID")
        try:
            p=subprocess.run(["npx","--yes","wrangler@latest",*args],cwd=str(cwd) if cwd else None,env=env,text=True,capture_output=True,timeout=max(self.timeout*6,120))
        except subprocess.TimeoutExpired as e:
            raise ConnectorError("Wrangler timed out") from e
        out=((p.stdout or "")+"\n"+(p.stderr or "")).strip()
        if p.returncode: raise ConnectorError(f"Wrangler failed ({p.returncode}): {out[-2000:]}")
        return out

    def _latest(self,project):
        a=env_value("CLOUDFLARE_ACCOUNT_ID")
        o=self._api("GET",f"/accounts/{parse.quote(a)}/pages/projects/{parse.quote(project)}/deployments?page=1&per_page=1")
        rows=(o or {}).get("result") or []
        return rows[0] if rows else {}

    def _receipt(self,r):
        root=Path(os.environ.get("COMPANYOS_HOME",str(Path.home()/"companyos")))
        d=root/".companyos_runtime"/"deployments"; d.mkdir(parents=True,exist_ok=True)
        fn=d/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+r.get("project_name","deployment")+"_cloudflare.json")
        safe={k:v for k,v in r.items() if "token" not in k.lower() and "secret" not in k.lower()}
        fn.write_text(json.dumps(safe,indent=2,sort_keys=True)+"\n")
        return str(fn)

    def _pages(self,p):
        project=self._slug(p); branch=str(p.get("branch") or "main")
        root,tmp=self._root(p)
        try:
            created=self._ensure_project(project,branch)
            self._wrangler(["pages","deploy",str(root),"--project-name",project,"--branch",branch,"--commit-dirty=true"])
            latest=self._latest(project)
            url=f"https://{project}.pages.dev" if branch=="main" else latest.get("url")
            r={"ok":True,"status":"deployment_created","provider":"cloudflare","mode":"pages",
               "project_name":project,"project_created":created,"deployment_id":latest.get("id"),
               "live_url":url,"environment":latest.get("environment") or ("production" if branch=="main" else "preview"),
               "created_on":latest.get("created_on"),"timestamp":datetime.now(timezone.utc).isoformat()}
            r["receipt_path"]=self._receipt(r); return r
        finally:
            if tmp: shutil.rmtree(root,ignore_errors=True)

    def _worker(self,p):
        entry=p.get("entrypoint") or p.get("worker_path") or p.get("path")
        if not entry: raise ConnectorError("worker deployment requires entrypoint/worker_path/path")
        entry=Path(str(entry)).expanduser()
        if not entry.is_absolute(): entry=Path.cwd()/entry
        if not entry.is_file(): raise ConnectorError(f"worker entrypoint not found: {entry}")
        project=self._slug(p)
        out=self._wrangler(["deploy",str(entry),"--name",project],cwd=entry.parent)
        urls=re.findall(r"https://[^\s]+",out)
        r={"ok":True,"status":"deployment_created","provider":"cloudflare","mode":"worker","project_name":project,
           "deployment_id":None,"live_url":urls[-1].rstrip(".,)") if urls else None,
           "timestamp":datetime.now(timezone.utc).isoformat()}
        r["receipt_path"]=self._receipt(r); return r

    def _execute(self,action,payload):
        if action not in {"deploy_production","deploy_preview","deploy_worker"}:
            return {"ok":False,"status":"unsupported_action","connector":"hosting","provider":"cloudflare","action":action}
        p=dict(payload or {})
        if action=="deploy_worker" or str(p.get("deployment_mode","")).lower()=="worker": return self._worker(p)
        if action=="deploy_preview" and "branch" not in p: p["branch"]="preview"
        return self._pages(p)
PY

cat > companyos/connectors_live/registry.py <<'PY'
import os
from .adapters import SMTPConnector, RESTConnector, HostingConnector as VercelHostingConnector, DomainConnector, CRMConnector, AccountingConnector, BankingConnector, CryptoConnector
from .cloudflare_adapter import CloudflareHostingConnector

def build_registry(config):
    g=config.get("global",{})
    def merged(name): return {**g,**config.get(name,{})}
    hc=merged("hosting")
    provider=str(os.environ.get("COMPANYOS_HOSTING_PROVIDER",hc.get("provider","cloudflare"))).lower().strip()
    hosting=VercelHostingConnector(hc) if provider=="vercel" else CloudflareHostingConnector(hc)
    return {
        "smtp":SMTPConnector(merged("smtp")),"rest_api":RESTConnector(merged("rest_api")),
        "hosting":hosting,"domains":DomainConnector(merged("domains")),"crm":CRMConnector(merged("crm")),
        "accounting":AccountingConnector(merged("accounting")),"banking":BankingConnector(merged("banking")),
        "crypto":CryptoConnector(merged("crypto")),
    }
PY

python - <<'PY'
import json
from pathlib import Path
p=Path("config/connectors.json")
cfg=json.loads(p.read_text()) if p.exists() else {}
h=cfg.setdefault("hosting",{})
h.update({"enabled":True,"provider":"cloudflare","token_env":"CLOUDFLARE_API_TOKEN","account_id_env":"CLOUDFLARE_ACCOUNT_ID","dry_run":False})
p.write_text(json.dumps(cfg,indent=2)+"\n")
PY

python - <<'PY'
from pathlib import Path
p=Path.home()/".companyos_launch_env"
lines=p.read_text().splitlines()
lines=[x for x in lines if not x.startswith("export COMPANYOS_HOSTING_PROVIDER=")]
lines.append("export COMPANYOS_HOSTING_PROVIDER=cloudflare")
p.write_text("\n".join(lines)+"\n"); p.chmod(0o600)
PY

cat > scripts/companyos_cloudflarectl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json, os, sys
from pathlib import Path
from urllib import error, request

def load_env():
    p=Path.home()/".companyos_launch_env"
    if not p.exists(): return
    for raw in p.read_text().splitlines():
        s=raw.strip()
        if s.startswith("export ") and "=" in s:
            k,v=s[7:].split("=",1); os.environ.setdefault(k.strip(),v.strip().strip("'\""))

def api(path):
    t=os.environ.get("CLOUDFLARE_API_TOKEN","")
    req=request.Request("https://api.cloudflare.com/client/v4"+path,headers={"Authorization":f"Bearer {t}","Content-Type":"application/json"})
    try:
        with request.urlopen(req,timeout=30) as r: return r.status,json.loads(r.read().decode() or "{}")
    except error.HTTPError as e:
        b=e.read().decode("utf-8","replace")
        try:o=json.loads(b)
        except:o={"raw":b[:1000]}
        return e.code,o

def main():
    load_env()
    cmd=sys.argv[1] if len(sys.argv)>1 else "status"
    token=os.environ.get("CLOUDFLARE_API_TOKEN",""); acct=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
    if cmd=="status":
        print(json.dumps({"provider":os.environ.get("COMPANYOS_HOSTING_PROVIDER","cloudflare"),
                          "token":"SET" if token else "MISSING","account_id":"SET" if acct else "MISSING",
                          "ready":bool(token and acct)},indent=2)); return
    if cmd=="verify":
        code,o=api("/user/tokens/verify")
        print(json.dumps({"http_status":code,"success":bool(o.get("success")),
                          "token_status":(o.get("result") or {}).get("status"),"errors":o.get("errors") or []},indent=2))
        raise SystemExit(0 if code==200 and o.get("success") else 1)
    if cmd=="projects":
        code,o=api(f"/accounts/{acct}/pages/projects")
        rows=o.get("result") or []
        print(json.dumps({"http_status":code,"success":bool(o.get("success")),"project_count":len(rows),
                          "projects":[{"name":x.get("name"),"subdomain":x.get("subdomain")} for x in rows[:25]],
                          "errors":o.get("errors") or []},indent=2))
        raise SystemExit(0 if code==200 and o.get("success") else 1)
    if cmd in {"demo","commission"}:
        root=Path.home()/"companyos"/".companyos_runtime"/"cloudflare_commissioning_site"; root.mkdir(parents=True,exist_ok=True)
        (root/"index.html").write_text("<!doctype html><meta charset=utf-8><title>CompanyOS PASS</title><h1>CompanyOS Cloudflare Hosting: PASS</h1><p>Harmless commissioning deployment.</p>")
        sys.path.insert(0,str(Path.home()/"companyos"))
        from companyos.connectors_live.cloudflare_adapter import CloudflareHostingConnector
        c=CloudflareHostingConnector({"enabled":True,"dry_run":False,"request_timeout_seconds":30,"max_retries":1})
        r=c.execute("deploy_production",{"project_name":"companyos-commissioning","website_path":str(root),"branch":"main"})
        print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("ok") else 1)
    print("Usage: companyos_cloudflarectl [status|verify|projects|demo]"); raise SystemExit(2)
main()
PY
chmod +x scripts/companyos_cloudflarectl

python -m py_compile companyos/connectors_live/cloudflare_adapter.py companyos/connectors_live/registry.py scripts/companyos_cloudflarectl

source "$ENV_FILE"
python - <<'PY'
import os
from pathlib import Path
p=Path.home()/".companyos_launch_env"
for raw in p.read_text().splitlines():
    s=raw.strip()
    if s.startswith("export ") and "=" in s:
        k,v=s[7:].split("=",1); os.environ.setdefault(k.strip(),v.strip().strip("'\""))
from companyos.connectors_live.config import load_config
from companyos.connectors_live.registry import build_registry
h=build_registry(load_config())["hosting"].health()
assert h["provider"]=="cloudflare",h
assert h["configured"] is True,h
assert h["dry_run"] is False,h
print("HOSTING_REGISTRY_PROVIDER=cloudflare")
print("HOSTING_CONFIGURED=true")
print("HOSTING_DRY_RUN=false")
PY

scripts/companyos_cloudflarectl verify
scripts/companyos_cloudflarectl projects

echo "Performing harmless real Cloudflare Pages commissioning deployment..."
scripts/companyos_cloudflarectl demo | tee "$ROOT/.companyos_runtime/cloudflare_commissioning_$STAMP.json"

if [ -x scripts/companyosctl ]; then scripts/companyosctl restart || true; fi
sleep 2

if git grep -nF "${CLOUDFLARE_API_TOKEN}" -- . ':!*.log' ':!.companyos_runtime' 2>/dev/null | head -1 | grep -q .; then
  echo "ERROR: Cloudflare token detected in source. Refusing commit."
  exit 1
fi
echo "SECRET_SCAN=PASS"

git add companyos/connectors_live/cloudflare_adapter.py companyos/connectors_live/registry.py config/connectors.json scripts/companyos_cloudflarectl
if ! git diff --cached --quiet; then
  git commit -m "Add Cloudflare as CompanyOS primary hosting provider"
fi
BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] && git push origin "$BRANCH" || true

echo
scripts/companyos_cloudflarectl status
echo "Backup: $BACKUP"
echo "Vercel retained as optional provider; Cloudflare is primary."
echo "Deployment receipts: $ROOT/.companyos_runtime/deployments"
echo "COMPANYOS_CLOUDFLARE_FULL_HOSTING_BUNDLE=PASS"
