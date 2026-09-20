#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a
: "${CLOUDFLARE_API_TOKEN:?missing}"
: "${CLOUDFLARE_ACCOUNT_ID:?missing}"
cp companyos/connectors/cloudflare_hosting.py ".companyos_runtime/cloudflare_hosting_pre_v2_$(date +%Y%m%d_%H%M%S).py"

python - <<'PY'
from pathlib import Path
p=Path("companyos/connectors/cloudflare_hosting.py")
s=p.read_text()
start=s.index("    def deploy_directory(")
end=s.index("\n    def health(", start)
new='    def _jwt_request(self, method, path, jwt, body=None):\n        h={"Authorization":f"Bearer {jwt}","Accept":"application/json"}\n        data=body\n        if isinstance(body,(dict,list)):\n            data=json.dumps(body).encode()\n            h["Content-Type"]="application/json"\n        req=urllib.request.Request(API+path,data=data,headers=h,method=method)\n        try:\n            with urllib.request.urlopen(req,timeout=60) as r:\n                raw=r.read().decode("utf-8","replace")\n        except urllib.error.HTTPError as e:\n            raw=e.read().decode("utf-8","replace")\n            raise CloudflareError(f"Cloudflare asset HTTP {e.code}: {raw[:1200]}")\n        obj=json.loads(raw or "{}")\n        if not obj.get("success",False):\n            raise CloudflareError("Cloudflare asset API error: "+json.dumps(obj.get("errors",[])))\n        return obj\n\n    @staticmethod\n    def _asset_hash(content):\n        import hashlib\n        return hashlib.md5(content).hexdigest()\n\n    def deploy_directory(self,project_name,directory,production_branch="main"):\n        import base64\n        root=Path(directory).expanduser().resolve()\n        if not root.is_dir():\n            raise CloudflareError(f"Site directory does not exist: {root}")\n        self.ensure_project(project_name,production_branch)\n        assets={}\n        manifest={}\n        for p in sorted(root.rglob("*")):\n            if not p.is_file():\n                continue\n            rel="/"+p.relative_to(root).as_posix()\n            content=p.read_bytes()\n            h=self._asset_hash(content)\n            manifest[rel]=h\n            assets[h]=(content,mimetypes.guess_type(p.name)[0] or "application/octet-stream")\n        if not assets:\n            raise CloudflareError("Site directory contains no files")\n        n=urllib.parse.quote(project_name,safe="")\n        jwt=self._request("GET",f"/accounts/{self.account_id}/pages/projects/{n}/upload-token").get("result",{}).get("jwt")\n        if not jwt:\n            raise CloudflareError("Cloudflare did not return a Pages upload JWT")\n        missing=self._jwt_request("POST","/pages/assets/check-missing",jwt,{"hashes":list(assets)}).get("result",[])\n        if missing:\n            batch=[]\n            for h in missing:\n                content,ctype=assets[h]\n                batch.append({"key":h,"value":base64.b64encode(content).decode(),"metadata":{"contentType":ctype},"base64":True})\n            self._jwt_request("POST","/pages/assets/upload",jwt,batch)\n        body,ctype=self._multipart({"branch":production_branch,"manifest":json.dumps(manifest,separators=(",",":"))},[])\n        r=self._request("POST",f"/accounts/{self.account_id}/pages/projects/{n}/deployments",body,{"Content-Type":ctype}).get("result",{})\n        return {"provider":"cloudflare","project":project_name,"deployment_id":r.get("id"),"url":r.get("url"),\n                "environment":r.get("environment"),"aliases":r.get("aliases") or [],"status":"submitted",\n                "asset_count":len(manifest),"uploaded_assets":len(missing)}\n'
p.write_text(s[:start]+new+s[end:])
print("PATCHED Cloudflare Pages Direct Upload V2")
PY

python -m py_compile companyos/connectors/cloudflare_hosting.py
python -m pytest -q tests/generated/test_cloudflare_hosting.py
echo "===== CLOUDFLARE HEALTH ====="
python scripts/companyos_cloudflarectl health
SITE=".companyos_runtime/cloudflare_commissioning_site"
mkdir -p "$SITE"
[ -f "$SITE/index.html" ] || printf '%s\n' '<!doctype html><title>CompanyOS</title><h1>CompanyOS Cloudflare commissioning</h1>' > "$SITE/index.html"
echo "===== DIRECT UPLOAD COMMISSIONING ====="
python scripts/companyos_cloudflarectl deploy "$SITE" --project companyos-commissioning --branch main | tee .companyos_runtime/cloudflare_commissioning_result_v2.json
echo "===== VERIFY PROJECT ====="
python - <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from companyos.connectors.cloudflare_hosting import CloudflareHosting
r=CloudflareHosting().project("companyos-commissioning")
print(json.dumps({"name":r.get("name"),"subdomain":r.get("subdomain"),
"latest_deployment_id":(r.get("latest_deployment") or {}).get("id"),
"latest_deployment_url":(r.get("latest_deployment") or {}).get("url")},indent=2))
PY
git status --short
echo "COMPANYOS_CLOUDFLARE_DIRECT_UPLOAD_V2=PASS"
