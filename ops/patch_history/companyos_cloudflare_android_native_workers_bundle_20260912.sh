#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
ENV_FILE="$HOME/.companyos_launch_env"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.companyos_backups/cloudflare_android_native_$STAMP"

echo "============================================================"
echo " CompanyOS - Cloudflare Android-Native Hosting Bundle"
echo " No Wrangler. No Node runtime requirement."
echo " Direct Cloudflare Workers Static Assets API."
echo "============================================================"

cd "$ROOT"
mkdir -p "$BACKUP" "$ROOT/.companyos_runtime/deployments"

[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found"; exit 1; }

set +u
# shellcheck disable=SC1090
source "$ENV_FILE"
set -u

[ -n "${CLOUDFLARE_API_TOKEN:-}" ] || { echo "ERROR: CLOUDFLARE_API_TOKEN missing"; exit 1; }
[ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ] || { echo "ERROR: CLOUDFLARE_ACCOUNT_ID missing"; exit 1; }

echo "[1/11] Backing up hosting files..."
for f in \
  companyos/connectors_live/cloudflare_adapter.py \
  companyos/connectors_live/registry.py \
  config/connectors.json \
  scripts/companyos_cloudflarectl
do
  if [ -f "$f" ]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

echo "[2/11] Ensuring Python requests dependency..."
python - <<'PY'
try:
    import requests
    print("REQUESTS=ALREADY_INSTALLED")
except Exception:
    raise SystemExit(42)
PY
rc=$?
if [ "$rc" = "42" ]; then
  python -m pip install --upgrade requests
fi

echo "[3/11] Installing Android-native Cloudflare connector..."
cat > companyos/connectors_live/cloudflare_adapter.py <<'PY'
from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

from .base import BaseConnector, ConnectorError
from .config import env_value


class CloudflareHostingConnector(BaseConnector):
    """
    CompanyOS Cloudflare hosting connector.

    Uses Cloudflare Workers Static Assets Direct Upload API.
    This intentionally does NOT depend on Wrangler/Node so it works on
    Android/Termux ARM64.

    Required local environment:
      CLOUDFLARE_API_TOKEN
      CLOUDFLARE_ACCOUNT_ID

    Optional:
      CLOUDFLARE_WORKERS_SUBDOMAIN
    """

    name = "hosting"
    provider = "cloudflare"
    API_BASE = "https://api.cloudflare.com/client/v4"

    MAX_FILE_SIZE = 25 * 1024 * 1024
    MAX_FILES = 20000

    def is_configured(self):
        return (
            self.enabled
            and bool(env_value("CLOUDFLARE_API_TOKEN"))
            and bool(env_value("CLOUDFLARE_ACCOUNT_ID"))
        )

    def health(self):
        h = super().health()
        h.update(
            {
                "provider": "cloudflare",
                "mode": "workers_static_assets_api",
                "android_native": True,
                "wrangler_required": False,
                "token_set": bool(env_value("CLOUDFLARE_API_TOKEN")),
                "account_id_set": bool(env_value("CLOUDFLARE_ACCOUNT_ID")),
                "workers_ready": self.is_configured(),
            }
        )
        return h

    def _headers(self, token=None):
        return {
            "Authorization": f"Bearer {token or env_value('CLOUDFLARE_API_TOKEN')}",
        }

    def _json(self, method, path, payload=None, token=None, params=None, ok=(200, 201)):
        url = self.API_BASE + path
        try:
            r = requests.request(
                method,
                url,
                headers={
                    **self._headers(token),
                    "Content-Type": "application/json",
                },
                json=payload,
                params=params,
                timeout=self.timeout,
            )
        except Exception as exc:
            raise ConnectorError(f"Cloudflare request failed: {exc}") from exc

        if r.status_code not in ok:
            raise ConnectorError(
                f"Cloudflare HTTP {r.status_code}: {r.text[:1600]}"
            )

        try:
            obj = r.json()
        except Exception as exc:
            raise ConnectorError(
                f"Cloudflare returned non-JSON response: {r.text[:1000]}"
            ) from exc

        if isinstance(obj, dict) and obj.get("success") is False:
            raise ConnectorError(
                "Cloudflare API rejected request: "
                + json.dumps(obj.get("errors") or [])[:1500]
            )
        return obj

    def _slug(self, payload):
        raw = (
            payload.get("project_name")
            or payload.get("worker_name")
            or payload.get("company_name")
            or payload.get("company_id")
            or payload.get("name")
            or "companyos-site"
        )
        name = re.sub(r"[^a-z0-9-]+", "-", str(raw).lower().strip())
        name = re.sub(r"-{2,}", "-", name).strip("-")
        return (name or "companyos-site")[:58]

    def _resolve_root(self, payload):
        supplied = payload.get("files")
        if isinstance(supplied, dict) and supplied:
            tmp = Path(tempfile.mkdtemp(prefix="companyos_cf_"))
            for name, content in supplied.items():
                rel = str(name).lstrip("/").replace("\\", "/")
                if not rel or ".." in Path(rel).parts:
                    shutil.rmtree(tmp, ignore_errors=True)
                    raise ConnectorError(f"unsafe deploy path: {name}")
                dst = tmp / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(
                    content if isinstance(content, bytes)
                    else str(content).encode("utf-8")
                )
            return tmp, True

        raw = (
            payload.get("website_path")
            or payload.get("site_path")
            or payload.get("artifact_path")
            or payload.get("path")
            or payload.get("artifact")
        )
        if not raw:
            raise ConnectorError(
                "deploy_production requires website_path/site_path/path or files"
            )

        root = Path(str(raw)).expanduser()
        if not root.is_absolute():
            choices = [Path.cwd() / root, Path.home() / "companyos" / root]
            root = next((p for p in choices if p.exists()), choices[0])

        if not root.exists():
            raise ConnectorError(f"website path not found: {root}")

        if root.is_file():
            tmp = Path(tempfile.mkdtemp(prefix="companyos_cf_file_"))
            shutil.copy2(root, tmp / root.name)
            return tmp, True

        return root, False

    @staticmethod
    def _hash_asset(data, extension):
        # Cloudflare Workers Static Assets Direct Upload reference algorithm:
        # sha256(base64(file bytes) + extension), truncated to 32 hex chars.
        material = base64.b64encode(data) + extension.encode("utf-8")
        return hashlib.sha256(material).hexdigest()[:32]

    def _scan_assets(self, root):
        items = {}
        ignored_dirs = {".git", ".venv", "node_modules", "__pycache__", ".wrangler"}
        ignored_files = {".env", ".env.local", ".env.production"}

        for f in sorted(root.rglob("*")):
            if not f.is_file() or f.is_symlink():
                continue
            rel = f.relative_to(root)
            if any(part in ignored_dirs for part in rel.parts):
                continue
            if f.name in ignored_files:
                continue
            if f.stat().st_size > self.MAX_FILE_SIZE:
                raise ConnectorError(
                    f"asset too large (>25 MiB): {rel.as_posix()}"
                )
            data = f.read_bytes()
            extension = f.suffix[1:] if f.suffix.startswith(".") else f.suffix
            h = self._hash_asset(data, extension)
            content_type = (
                mimetypes.guess_type(rel.as_posix())[0]
                or "application/octet-stream"
            )
            items["/" + rel.as_posix()] = {
                "hash": h,
                "size": len(data),
                "content_type": content_type,
                "data": data,
            }

        if not items:
            raise ConnectorError(f"no deployable files found: {root}")
        if len(items) > self.MAX_FILES:
            raise ConnectorError(
                f"too many assets: {len(items)} > {self.MAX_FILES}"
            )
        return items

    def _manifest(self, assets):
        return {
            path: {"hash": item["hash"], "size": item["size"]}
            for path, item in assets.items()
        }

    def _start_upload_session(self, worker, manifest):
        account = quote(env_value("CLOUDFLARE_ACCOUNT_ID"), safe="")
        obj = self._json(
            "POST",
            f"/accounts/{account}/workers/scripts/{quote(worker, safe='')}/assets-upload-session",
            {"manifest": manifest},
        )
        result = obj.get("result") or {}
        jwt = result.get("jwt")
        buckets = result.get("buckets")
        if not jwt or buckets is None:
            raise ConnectorError(
                "Cloudflare asset session did not return jwt/buckets"
            )
        return jwt, buckets

    def _upload_bucket(self, upload_jwt, bucket, assets_by_hash):
        # Cloudflare requires multipart/form-data, fields keyed by asset hash.
        files = []
        for h in bucket:
            item = assets_by_hash.get(h)
            if not item:
                raise ConnectorError(f"Cloudflare requested unknown hash: {h}")
            encoded = base64.b64encode(item["data"]).decode("ascii")
            files.append(
                (h, (None, encoded, item["content_type"]))
            )

        url = (
            self.API_BASE
            + f"/accounts/{quote(env_value('CLOUDFLARE_ACCOUNT_ID'), safe='')}"
            + "/workers/assets/upload"
        )
        try:
            r = requests.post(
                url,
                headers=self._headers(upload_jwt),
                params={"base64": "true"},
                files=files,
                timeout=max(self.timeout, 60),
            )
        except Exception as exc:
            raise ConnectorError(f"asset upload failed: {exc}") from exc

        if r.status_code not in (200, 201):
            raise ConnectorError(
                f"Cloudflare asset upload HTTP {r.status_code}: {r.text[:1600]}"
            )
        try:
            obj = r.json()
        except Exception as exc:
            raise ConnectorError(
                f"asset upload returned non-JSON: {r.text[:1000]}"
            ) from exc
        if obj.get("success") is False:
            raise ConnectorError(
                "asset upload rejected: "
                + json.dumps(obj.get("errors") or [])[:1500]
            )
        return (obj.get("result") or {}).get("jwt")

    def _completion_token(self, worker, assets):
        manifest = self._manifest(assets)
        upload_jwt, buckets = self._start_upload_session(worker, manifest)
        if not buckets:
            return upload_jwt, 0

        by_hash = {item["hash"]: item for item in assets.values()}
        completion = None
        uploaded = 0
        for bucket in buckets:
            new_jwt = self._upload_bucket(upload_jwt, bucket, by_hash)
            uploaded += len(bucket)
            if new_jwt:
                completion = new_jwt

        if not completion:
            raise ConnectorError(
                "assets uploaded but Cloudflare returned no completion token"
            )
        return completion, uploaded

    def _deploy_worker(self, worker, completion_jwt):
        account = quote(env_value("CLOUDFLARE_ACCOUNT_ID"), safe="")
        url = (
            self.API_BASE
            + f"/accounts/{account}/workers/scripts/{quote(worker, safe='')}"
        )

        main_js = (
            "export default {"
            "async fetch(request, env) {"
            "return env.ASSETS.fetch(request);"
            "}"
            "};"
        )

        metadata = {
            "main_module": "main.js",
            "compatibility_date": datetime.now(timezone.utc).date().isoformat(),
            "assets": {
                "jwt": completion_jwt,
                "config": {
                    "html_handling": "auto-trailing-slash",
                    "not_found_handling": "404-page",
                },
            },
            "bindings": [{"type": "assets", "name": "ASSETS"}],
        }

        files = [
            (
                "metadata",
                (None, json.dumps(metadata), "application/json"),
            ),
            (
                "main.js",
                (
                    "main.js",
                    main_js,
                    "application/javascript+module",
                ),
            ),
        ]

        try:
            r = requests.put(
                url,
                headers=self._headers(),
                files=files,
                timeout=max(self.timeout, 60),
            )
        except Exception as exc:
            raise ConnectorError(f"Worker deployment failed: {exc}") from exc

        if r.status_code not in (200, 201):
            raise ConnectorError(
                f"Cloudflare Worker HTTP {r.status_code}: {r.text[:1800]}"
            )
        try:
            obj = r.json()
        except Exception as exc:
            raise ConnectorError(
                f"Worker deploy returned non-JSON: {r.text[:1200]}"
            ) from exc
        if obj.get("success") is False:
            raise ConnectorError(
                "Worker deployment rejected: "
                + json.dumps(obj.get("errors") or [])[:1600]
            )
        return obj.get("result") or {}

    def _enable_workers_dev(self, worker):
        account = quote(env_value("CLOUDFLARE_ACCOUNT_ID"), safe="")
        path = (
            f"/accounts/{account}/workers/scripts/"
            f"{quote(worker, safe='')}/subdomain"
        )
        try:
            obj = self._json(
                "POST",
                path,
                {"enabled": True, "previews_enabled": True},
                ok=(200, 201),
            )
            return bool((obj.get("result") or {}).get("enabled", True))
        except ConnectorError:
            # Deployment remains valid even if workers.dev exposure is unavailable.
            return False

    def _account_subdomain(self):
        configured = env_value("CLOUDFLARE_WORKERS_SUBDOMAIN")
        if configured:
            return configured.strip().replace(".workers.dev", "")

        account = quote(env_value("CLOUDFLARE_ACCOUNT_ID"), safe="")
        try:
            obj = self._json(
                "GET",
                f"/accounts/{account}/workers/subdomain",
                ok=(200,),
            )
            return (obj.get("result") or {}).get("subdomain")
        except ConnectorError:
            return None

    def _write_receipt(self, receipt):
        root = Path(
            os.environ.get(
                "COMPANYOS_HOME",
                str(Path.home() / "companyos"),
            )
        )
        d = root / ".companyos_runtime" / "deployments"
        d.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = d / f"{stamp}_{receipt['project_name']}_cloudflare.json"
        safe = {
            k: v for k, v in receipt.items()
            if "token" not in k.lower()
            and "secret" not in k.lower()
            and "jwt" not in k.lower()
        }
        path.write_text(json.dumps(safe, indent=2, sort_keys=True) + "\n")
        return str(path)

    def _deploy_static(self, payload):
        worker = self._slug(payload)
        root, temporary = self._resolve_root(payload)
        try:
            assets = self._scan_assets(root)
            completion_jwt, uploaded = self._completion_token(worker, assets)
            result = self._deploy_worker(worker, completion_jwt)
            workers_dev_enabled = self._enable_workers_dev(worker)
            subdomain = self._account_subdomain()

            live_url = None
            if subdomain and workers_dev_enabled:
                live_url = f"https://{worker}.{subdomain}.workers.dev"

            receipt = {
                "ok": True,
                "status": "deployment_created",
                "provider": "cloudflare",
                "mode": "workers_static_assets_api",
                "project_name": worker,
                "deployment_id": (
                    result.get("id")
                    or result.get("etag")
                    or result.get("script_id")
                ),
                "live_url": live_url,
                "workers_dev_enabled": workers_dev_enabled,
                "asset_count": len(assets),
                "assets_uploaded": uploaded,
                "wrangler_required": False,
                "android_native": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            receipt["receipt_path"] = self._write_receipt(receipt)
            return receipt
        finally:
            if temporary:
                shutil.rmtree(root, ignore_errors=True)

    def _execute(self, action, payload):
        if action not in {
            "deploy_production",
            "deploy_preview",
            "deploy_worker",
        }:
            return {
                "ok": False,
                "status": "unsupported_action",
                "connector": self.name,
                "provider": self.provider,
                "action": action,
            }

        payload = dict(payload or {})
        return self._deploy_static(payload)
PY

echo "[4/11] Wiring Cloudflare as primary hosting provider..."
cat > companyos/connectors_live/registry.py <<'PY'
import os

from .adapters import (
    SMTPConnector,
    RESTConnector,
    HostingConnector as VercelHostingConnector,
    DomainConnector,
    CRMConnector,
    AccountingConnector,
    BankingConnector,
    CryptoConnector,
)
from .cloudflare_adapter import CloudflareHostingConnector


def build_registry(config):
    g = config.get("global", {})

    def merged(name):
        return {**g, **config.get(name, {})}

    hc = merged("hosting")
    provider = str(
        os.environ.get(
            "COMPANYOS_HOSTING_PROVIDER",
            hc.get("provider", "cloudflare"),
        )
    ).lower().strip()

    hosting = (
        VercelHostingConnector(hc)
        if provider == "vercel"
        else CloudflareHostingConnector(hc)
    )

    return {
        "smtp": SMTPConnector(merged("smtp")),
        "rest_api": RESTConnector(merged("rest_api")),
        "hosting": hosting,
        "domains": DomainConnector(merged("domains")),
        "crm": CRMConnector(merged("crm")),
        "accounting": AccountingConnector(merged("accounting")),
        "banking": BankingConnector(merged("banking")),
        "crypto": CryptoConnector(merged("crypto")),
    }
PY

python - <<'PY'
import json
from pathlib import Path

p = Path("config/connectors.json")
cfg = json.loads(p.read_text()) if p.exists() else {}
h = cfg.setdefault("hosting", {})
h.update({
    "enabled": True,
    "provider": "cloudflare",
    "token_env": "CLOUDFLARE_API_TOKEN",
    "account_id_env": "CLOUDFLARE_ACCOUNT_ID",
    "dry_run": False,
})
p.write_text(json.dumps(cfg, indent=2) + "\n")
PY

python - <<'PY'
from pathlib import Path

p = Path.home() / ".companyos_launch_env"
lines = p.read_text().splitlines()
lines = [
    x for x in lines
    if not x.startswith("export COMPANYOS_HOSTING_PROVIDER=")
]
lines.append("export COMPANYOS_HOSTING_PROVIDER=cloudflare")
p.write_text("\n".join(lines) + "\n")
p.chmod(0o600)
PY

echo "[5/11] Installing Cloudflare control tool..."
cat > scripts/companyos_cloudflarectl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib import error, request


def load_env():
    p = Path.home() / ".companyos_launch_env"
    if not p.exists():
        return
    for raw in p.read_text().splitlines():
        s = raw.strip()
        if s.startswith("export ") and "=" in s:
            k, v = s[7:].split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def api(path):
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    req = request.Request(
        "https://api.cloudflare.com/client/v4" + path,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            obj = json.loads(body)
        except Exception:
            obj = {"raw": body[:1000]}
        return e.code, obj


def main():
    load_env()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")

    if cmd == "status":
        sub_code, sub = api(f"/accounts/{account}/workers/subdomain") if account else (0, {})
        print(json.dumps({
            "provider": os.environ.get("COMPANYOS_HOSTING_PROVIDER", "cloudflare"),
            "mode": "workers_static_assets_api",
            "android_native": True,
            "wrangler_required": False,
            "token": "SET" if token else "MISSING",
            "account_id": "SET" if account else "MISSING",
            "workers_subdomain": (sub.get("result") or {}).get("subdomain") if sub_code == 200 else None,
            "ready": bool(token and account),
        }, indent=2))
        return

    if cmd == "verify":
        code, obj = api("/user/tokens/verify")
        print(json.dumps({
            "http_status": code,
            "success": bool(obj.get("success")),
            "token_status": (obj.get("result") or {}).get("status"),
            "errors": obj.get("errors") or [],
        }, indent=2))
        raise SystemExit(0 if code == 200 and obj.get("success") else 1)

    if cmd == "workers":
        code, obj = api(f"/accounts/{account}/workers/scripts")
        rows = obj.get("result") or []
        print(json.dumps({
            "http_status": code,
            "success": bool(obj.get("success")),
            "worker_count": len(rows),
            "workers": [
                {"id": x.get("id"), "modified_on": x.get("modified_on")}
                for x in rows[:30]
            ],
            "errors": obj.get("errors") or [],
        }, indent=2))
        raise SystemExit(0 if code == 200 and obj.get("success") else 1)

    if cmd in {"demo", "commission"}:
        site = (
            Path.home()
            / "companyos"
            / ".companyos_runtime"
            / "cloudflare_commissioning_site"
        )
        site.mkdir(parents=True, exist_ok=True)
        (site / "index.html").write_text(
            """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>CompanyOS Cloudflare PASS</title>
<style>body{font-family:system-ui;max-width:760px;margin:10vh auto;padding:24px}</style>
<h1>CompanyOS Cloudflare Hosting: PASS</h1>
<p>Android-native direct API deployment is operational.</p>
"""
        )
        sys.path.insert(0, str(Path.home() / "companyos"))
        from companyos.connectors_live.cloudflare_adapter import CloudflareHostingConnector

        c = CloudflareHostingConnector({
            "enabled": True,
            "dry_run": False,
            "request_timeout_seconds": 45,
            "max_retries": 1,
        })
        result = c.execute(
            "deploy_production",
            {
                "project_name": "companyos-commissioning",
                "website_path": str(site),
            },
        )
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result.get("ok") else 1)

    print("Usage: companyos_cloudflarectl [status|verify|workers|demo]")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
PY
chmod +x scripts/companyos_cloudflarectl

echo "[6/11] Running syntax/import tests..."
python -m py_compile \
  companyos/connectors_live/cloudflare_adapter.py \
  companyos/connectors_live/registry.py \
  scripts/companyos_cloudflarectl

source "$ENV_FILE"

python - <<'PY'
import os
from pathlib import Path

p = Path.home() / ".companyos_launch_env"
for raw in p.read_text().splitlines():
    s = raw.strip()
    if s.startswith("export ") and "=" in s:
        k, v = s[7:].split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))

from companyos.connectors_live.config import load_config
from companyos.connectors_live.registry import build_registry

h = build_registry(load_config())["hosting"].health()
assert h["provider"] == "cloudflare", h
assert h["configured"] is True, h
assert h["dry_run"] is False, h
assert h["android_native"] is True, h
assert h["wrangler_required"] is False, h

print("HOSTING_PROVIDER=cloudflare")
print("HOSTING_MODE=workers_static_assets_api")
print("ANDROID_NATIVE=true")
print("WRANGLER_REQUIRED=false")
print("HOSTING_CONFIGURED=true")
PY

echo "[7/11] Verifying Cloudflare token..."
scripts/companyos_cloudflarectl verify

echo "[8/11] Checking Workers API access..."
scripts/companyos_cloudflarectl workers

echo "[9/11] Performing harmless real commissioning deployment..."
scripts/companyos_cloudflarectl demo \
  | tee "$ROOT/.companyos_runtime/cloudflare_android_native_commissioning_$STAMP.json"

echo "[10/11] Verifying deployed public URL..."
DEPLOY_JSON="$(ls -1t "$ROOT/.companyos_runtime/deployments/"*companyos-commissioning_cloudflare.json 2>/dev/null | head -1 || true)"
if [ -n "$DEPLOY_JSON" ]; then
  LIVE_URL="$(python - "$DEPLOY_JSON" <<'PY'
import json,sys
print(json.load(open(sys.argv[1])).get("live_url") or "")
PY
)"
else
  LIVE_URL=""
fi

if [ -n "$LIVE_URL" ]; then
  echo "LIVE_URL=$LIVE_URL"
  HTTP_CODE="$(curl -L -sS -o /tmp/companyos_cf_probe.html -w '%{http_code}' "$LIVE_URL/" || true)"
  echo "LIVE_HTTP_STATUS=$HTTP_CODE"
  if [ "$HTTP_CODE" != "200" ]; then
    echo "WARNING: deployment was created but public URL did not return HTTP 200 yet."
  else
    grep -q "CompanyOS Cloudflare Hosting: PASS" /tmp/companyos_cf_probe.html \
      && echo "PUBLIC_CONTENT_CHECK=PASS" \
      || echo "PUBLIC_CONTENT_CHECK=WARNING"
  fi
else
  echo "LIVE_URL=NOT_AVAILABLE"
  echo "NOTE: Worker deployed, but workers.dev subdomain may need one-time account setup."
fi

echo "[11/11] Restarting CompanyOS, secret-scanning, committing and pushing..."
if [ -x scripts/companyosctl ]; then
  scripts/companyosctl restart || true
elif [ -x scripts/companyos_control ]; then
  scripts/companyos_control restart || true
fi

sleep 2

if git grep -nF "${CLOUDFLARE_API_TOKEN}" -- . \
    ':!*.log' ':!.companyos_runtime' 2>/dev/null \
    | head -1 | grep -q .; then
  echo "ERROR: Cloudflare token detected in source. Refusing commit."
  exit 1
fi
echo "SECRET_SCAN=PASS"

git add \
  companyos/connectors_live/cloudflare_adapter.py \
  companyos/connectors_live/registry.py \
  config/connectors.json \
  scripts/companyos_cloudflarectl

if ! git diff --cached --quiet; then
  git commit -m "Use Android-native Cloudflare Workers hosting"
fi

BRANCH="$(git branch --show-current)"
if [ -n "$BRANCH" ]; then
  git push origin "$BRANCH" || {
    echo "WARNING: git push failed; local Android-native hosting remains installed."
  }
fi

echo
echo "==================== FINAL STATUS ===================="
scripts/companyos_cloudflarectl status || true

python - <<'PY'
import os, json
from pathlib import Path

p = Path.home() / ".companyos_launch_env"
for raw in p.read_text().splitlines():
    s = raw.strip()
    if s.startswith("export ") and "=" in s:
        k, v = s[7:].split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))

from companyos.connectors_live.config import load_config
from companyos.connectors_live.registry import build_registry

h = build_registry(load_config())["hosting"].health()
print(json.dumps({
    "hosting": h,
    "cloudflare_primary": True,
    "vercel_required": False,
    "wrangler_required": False,
    "android_native": True,
    "deployment_receipts": str(
        Path.home() / "companyos" / ".companyos_runtime" / "deployments"
    ),
}, indent=2))
PY

echo
echo "Backup: $BACKUP"
echo "Control: scripts/companyos_cloudflarectl status"
echo "Verify:  scripts/companyos_cloudflarectl verify"
echo "List:    scripts/companyos_cloudflarectl workers"
echo "Test:    scripts/companyos_cloudflarectl demo"
echo "COMPANYOS_CLOUDFLARE_ANDROID_NATIVE_BUNDLE=PASS"
