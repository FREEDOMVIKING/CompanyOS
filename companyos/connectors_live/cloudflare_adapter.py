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
