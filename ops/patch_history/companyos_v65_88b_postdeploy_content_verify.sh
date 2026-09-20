#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.88B POST-DEPLOY CONTENT VERIFY ====="
echo "ACTION=VERIFY_EXISTING_LATEST_DEPLOYMENT_ONLY"
echo "REDEPLOY=NO"
echo "ANALYTICS=STILL_PENDING_PERMISSION"

python - <<'PY'
from pathlib import Path
import json
import time
import urllib.request

HOME = Path.home()
ROOT = HOME / "companyos"
GLOBAL_RT = HOME / ".companyos_runtime"
LOCAL_RT = ROOT / ".companyos_runtime"
REPORT_DIR = GLOBAL_RT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(path).read_text(errors="ignore"))
    except Exception:
        return default

tracking = load_json(LOCAL_RT / "live_validation_tracking.json", {})
latest = load_json(LOCAL_RT / "live_validation_latest.json", {})

project_name = (
    tracking.get("project_name")
    or "companyos-regional-construction-ai"
)

from companyos.connectors.cloudflare_hosting import CloudflareHosting

cf = CloudflareHosting()
if not cf.configured:
    raise SystemExit("V65_88B_ABORT=cloudflare_not_configured")

project = cf.project(project_name)
latest_deploy = project.get("latest_deployment") or {}
canonical = project.get("canonical_deployment") or {}

def norm(url):
    if not url:
        return None
    s = str(url).strip()
    if not s:
        return None
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    return s.rstrip("/")

urls = []

def add(label, url):
    u = norm(url)
    if u and all(existing[1] != u for existing in urls):
        urls.append((label, u))

add("latest_deployment", latest_deploy.get("url"))
for a in latest_deploy.get("aliases") or []:
    add("latest_alias", a)
add("project_subdomain", project.get("subdomain"))
for d in project.get("domains") or []:
    add("project_domain", d)
add("canonical_deployment", canonical.get("url"))
add("previous_public_url", latest.get("public_url"))
add("tracking_public_url", tracking.get("stable_public_url"))

print("PROJECT_NAME=", project_name)
print("LATEST_DEPLOYMENT_ID=", latest_deploy.get("id"))
print("LATEST_DEPLOYMENT_URL=", latest_deploy.get("url"))
print("PROJECT_SUBDOMAIN=", project.get("subdomain"))
print("URL_CANDIDATES=", urls)

if not urls:
    raise SystemExit("V65_88B_ABORT=no_urls_to_verify")

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent":"CompanyOS-V65.88B/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", "replace")
        return int(resp.status), body

deadline = time.time() + 180
results = {}
content_url = None
stable_url = norm(project.get("subdomain"))

while time.time() < deadline:
    all_good = False

    for label, base in urls:
        row = results.setdefault(base, {"label": label})
        try:
            rs, rb = fetch(base + "/")
            is_, ib = fetch(base + "/interest.html")

            root_cta = (
                'href="/interest.html"' in rb
                or "V65.88 CTA BEGIN" in rb
            )
            interest_ok = (
                "Interest recorded." in ib
                or "positive-interest signal" in ib
            )

            row.update({
                "root_status": rs,
                "interest_status": is_,
                "root_has_cta": root_cta,
                "interest_page_ok": interest_ok,
            })

            print(
                "VERIFY=",
                label,
                base,
                "root_status=", rs,
                "interest_status=", is_,
                "root_has_cta=", root_cta,
                "interest_page_ok=", interest_ok,
            )

            if root_cta and interest_ok and content_url is None:
                content_url = base

            if stable_url and base == stable_url and root_cta and interest_ok:
                all_good = True

        except Exception as exc:
            row["error"] = f"{type(exc).__name__}:{exc}"
            print("VERIFY_WAIT=", label, base, row["error"])

    if all_good:
        break

    if content_url and not stable_url:
        break

    time.sleep(10)

if content_url is None:
    report = {
        "version": "V65.88B",
        "verified": False,
        "project_name": project_name,
        "latest_deployment_id": latest_deploy.get("id"),
        "results": results,
        "timestamp_unix": time.time(),
    }
    rp = REPORT_DIR / f"v65_88b_content_verify_{int(time.time())}.json"
    rp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("REPORT=", rp)
    raise SystemExit("V65_88B_FAIL=new_deployment_content_not_visible")

stable_ok = False
if stable_url and stable_url in results:
    r = results[stable_url]
    stable_ok = bool(r.get("root_has_cta") and r.get("interest_page_ok"))

record = {
    "schema": "companyos.live_validation_tracking.v1",
    "version": "V65.88B",
    "timestamp_unix": time.time(),
    "candidate_name": tracking.get("candidate_name") or latest.get("candidate_name"),
    "project_name": project_name,
    "latest_deployment_id": latest_deploy.get("id"),
    "latest_deployment_url": norm(latest_deploy.get("url")),
    "verified_content_url": content_url,
    "stable_public_url": stable_url or content_url,
    "stable_alias_updated": stable_ok,
    "conversion_url": (stable_url or content_url) + "/interest.html",
    "cta_installed": True,
    "analytics_enabled": False,
    "analytics_blocker": "cloudflare_api_token_missing_account_settings_permissions",
    "required_cloudflare_permissions": [
        "Account Settings Read",
        "Account Settings Write",
    ],
    "verification_results": results,
    "financial_actions": False,
    "outreach": False,
    "wallet_signing": False,
    "domain_purchase": False,
}

tracking_path = LOCAL_RT / "live_validation_tracking.json"
tracking_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

rp = REPORT_DIR / f"v65_88b_content_verify_{int(time.time())}.json"
rp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

print("VERIFIED_CONTENT_URL=", content_url)
print("STABLE_PUBLIC_URL=", stable_url or content_url)
print("STABLE_ALIAS_UPDATED=", stable_ok)
print("CONVERSION_URL=", record["conversion_url"])
print("REPORT=", rp)

print("V65_88B_LATEST_DEPLOYMENT_CONTENT=PASS")
if stable_ok:
    print("V65_88B_STABLE_ALIAS_CONTENT=PASS")
else:
    print("V65_88B_STABLE_ALIAS_CONTENT=PENDING_PROPAGATION")
print("V65_88B_CTA=PASS")
print("V65_88B_INTEREST_PAGE=PASS")
print("V65_88B_COMPLETE")
PY
