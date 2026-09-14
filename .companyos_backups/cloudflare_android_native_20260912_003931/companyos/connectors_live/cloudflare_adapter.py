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
