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

    def _jwt_request(self, method, path, jwt, body=None):
        h={"Authorization":f"Bearer {jwt}","Accept":"application/json"}
        data=body
        if isinstance(body,(dict,list)):
            data=json.dumps(body).encode()
            h["Content-Type"]="application/json"
        req=urllib.request.Request(API+path,data=data,headers=h,method=method)
        try:
            with urllib.request.urlopen(req,timeout=60) as r:
                raw=r.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            raw=e.read().decode("utf-8","replace")
            raise CloudflareError(f"Cloudflare asset HTTP {e.code}: {raw[:1200]}")
        obj=json.loads(raw or "{}")
        if not obj.get("success",False):
            raise CloudflareError("Cloudflare asset API error: "+json.dumps(obj.get("errors",[])))
        return obj

    @staticmethod
    def _asset_hash(content):
        import hashlib
        return hashlib.md5(content).hexdigest()

    def deploy_directory(self,project_name,directory,production_branch="main"):
        import base64
        root=Path(directory).expanduser().resolve()
        if not root.is_dir():
            raise CloudflareError(f"Site directory does not exist: {root}")
        self.ensure_project(project_name,production_branch)
        assets={}
        manifest={}
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            rel="/"+p.relative_to(root).as_posix()
            content=p.read_bytes()
            h=self._asset_hash(content)
            manifest[rel]=h
            assets[h]=(content,mimetypes.guess_type(p.name)[0] or "application/octet-stream")
        if not assets:
            raise CloudflareError("Site directory contains no files")
        n=urllib.parse.quote(project_name,safe="")
        jwt=self._request("GET",f"/accounts/{self.account_id}/pages/projects/{n}/upload-token").get("result",{}).get("jwt")
        if not jwt:
            raise CloudflareError("Cloudflare did not return a Pages upload JWT")
        missing=self._jwt_request("POST","/pages/assets/check-missing",jwt,{"hashes":list(assets)}).get("result",[])
        if missing:
            batch=[]
            for h in missing:
                content,ctype=assets[h]
                batch.append({"key":h,"value":base64.b64encode(content).decode(),"metadata":{"contentType":ctype},"base64":True})
            self._jwt_request("POST","/pages/assets/upload",jwt,batch)
        body,ctype=self._multipart({"branch":production_branch,"manifest":json.dumps(manifest,separators=(",",":"))},[])
        r=self._request("POST",f"/accounts/{self.account_id}/pages/projects/{n}/deployments",body,{"Content-Type":ctype}).get("result",{})
        return {"provider":"cloudflare","project":project_name,"deployment_id":r.get("id"),"url":r.get("url"),
                "environment":r.get("environment"),"aliases":r.get("aliases") or [],"status":"submitted",
                "asset_count":len(manifest),"uploaded_assets":len(missing)}

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
