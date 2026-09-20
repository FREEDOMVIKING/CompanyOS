#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.88A CTA FALLBACK + REDEPLOY ====="
echo "PURPOSE=KEEP_LIVE_VALIDATION_MOVING_WITHOUT_RUM_API_PERMISSION"
echo "FINANCIAL_ACTIONS=DISABLED"
echo "OUTREACH=DISABLED"
echo "WALLET_SIGNING=DISABLED"
echo "DOMAIN_PURCHASE=DISABLED"

python - <<'PY'
from pathlib import Path
import json
import re
import shutil
import time
import urllib.parse
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

latest = load_json(LOCAL_RT / "live_validation_latest.json", {})
if not latest:
    raise SystemExit("V65_88A_ABORT=live_validation_latest_missing")

public_url = str(latest.get("public_url") or "").strip()
candidate_name = str(
    latest.get("candidate_name")
    or latest.get("venture_title")
    or "Regional Construction AI"
).strip()

if not public_url:
    raise SystemExit("V65_88A_ABORT=public_url_missing")

parsed = urllib.parse.urlparse(public_url)
hostname = parsed.netloc or parsed.path.split("/")[0]
slug = re.sub(r"[^a-z0-9]+", "-", candidate_name.lower()).strip("-")[:60] or "regional-construction-ai"

site_candidates = [
    ROOT / "companyos_runtime" / "live_validation" / slug,
    ROOT / "companyos_runtime" / "live_validation" / "regional-construction-ai",
]
site_dir = next((p for p in site_candidates if (p / "index.html").exists()), None)
if site_dir is None:
    raise SystemExit("V65_88A_ABORT=live_site_source_not_found")

index_path = site_dir / "index.html"
interest_path = site_dir / "interest.html"

from companyos.connectors.cloudflare_hosting import CloudflareHosting
cf = CloudflareHosting()
if not cf.configured:
    raise SystemExit("V65_88A_ABORT=cloudflare_not_configured")

projects = cf.list_projects()
project = None
for p in projects:
    domains = set(str(x) for x in (p.get("domains") or []))
    subdomain = str(p.get("subdomain") or "")
    if hostname == subdomain or hostname in domains:
        project = p
        break

project_name = (
    (project or {}).get("name")
    or ("companyos-" + slug)[:58]
)

print("PUBLIC_URL_BEFORE=", public_url)
print("HOSTNAME=", hostname)
print("CANDIDATE_NAME=", candidate_name)
print("PROJECT_NAME=", project_name)
print("SITE_DIR=", site_dir)

# Backup source before modification.
backup_dir = GLOBAL_RT / "checkpoints" / f"v65_88a_site_before_{int(time.time())}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(index_path, backup_dir / "index.html")
if interest_path.exists():
    shutil.copy2(interest_path, backup_dir / "interest.html")
print("SITE_BACKUP_DIR=", backup_dir)

# Idempotently install a real CTA path.
page = index_path.read_text(encoding="utf-8")
page = re.sub(
    r"<!-- V65\.88 CTA BEGIN -->.*?<!-- V65\.88 CTA END -->",
    "",
    page,
    flags=re.S,
)

cta = r"""
<!-- V65.88 CTA BEGIN -->
<div class="card" id="early-access">
  <div class="label">Live validation</div>
  <div class="value">Would this save you time or money on construction planning, estimating, or coordination?</div>
  <p style="margin:18px 0 0">
    <a id="interest-cta"
       href="/interest.html"
       style="display:inline-block;padding:14px 20px;border-radius:12px;background:#f6f7f8;color:#0b0d10;text-decoration:none;font-weight:700">
       Yes - I'm interested
    </a>
  </p>
  <p style="font-size:13px;color:#8e98a6;margin-top:12px">
    This is an early market-validation test. No purchase is required.
  </p>
</div>
<!-- V65.88 CTA END -->
"""

if "</main>" not in page:
    raise SystemExit("V65_88A_ABORT=index_main_anchor_missing")
page = page.replace("</main>", cta + "\n</main>", 1)
index_path.write_text(page, encoding="utf-8")

interest_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Interest Recorded - {candidate_name}</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#0b0d10;color:#f6f7f8}}
main{{max-width:720px;margin:auto;padding:84px 24px}}
.badge{{display:inline-block;padding:7px 11px;border:1px solid #525861;border-radius:999px;font-size:13px}}
h1{{font-size:48px;line-height:1.05;margin:28px 0 16px}}
p{{font-size:20px;line-height:1.5;color:#c8cdd4}}
a{{color:#fff}}
</style>
</head>
<body>
<main>
<span class="badge">CompanyOS live validation</span>
<h1>Interest recorded.</h1>
<p>
This page represents a positive-interest signal for the
{candidate_name} validation experiment.
</p>
<p><a href="/">Back to the validation page</a></p>
</main>
</body>
</html>
"""
interest_path.write_text(interest_html, encoding="utf-8")

root_text = index_path.read_text(encoding="utf-8")
checks = {
    "root_has_cta": 'href="/interest.html"' in root_text,
    "interest_page_exists": interest_path.exists(),
}
print("STATIC_CHECKS=", checks)
if not all(checks.values()):
    raise SystemExit("V65_88A_FAIL=static_cta_check")

# Deploy same Pages project. No RUM API call.
start = time.perf_counter()
receipt = cf.deploy_directory(project_name, str(site_dir), "main")
deploy_seconds = round(time.perf_counter() - start, 3)

print("DEPLOY_SECONDS=", deploy_seconds)
print("DEPLOY_RECEIPT=", receipt)

stable_url = public_url
for alias in receipt.get("aliases") or []:
    alias = str(alias)
    if project_name + ".pages.dev" in alias:
        stable_url = alias
        break

if not stable_url.startswith(("http://", "https://")):
    stable_url = "https://" + stable_url

def probe(url, tries=20):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"CompanyOS-V65.88A/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8", "replace")
                if 200 <= int(resp.status) < 400:
                    return int(resp.status), body
        except Exception as exc:
            last = f"{type(exc).__name__}:{exc}"
        time.sleep(3)
    raise RuntimeError(last or "probe_failed")

root_status, root_body = probe(stable_url.rstrip("/") + "/")
interest_status, interest_body = probe(stable_url.rstrip("/") + "/interest.html")

print("ROOT_HTTP_STATUS=", root_status)
print("INTEREST_HTTP_STATUS=", interest_status)
print("LIVE_ROOT_HAS_CTA=", 'href="/interest.html"' in root_body)
print("LIVE_INTEREST_PAGE_OK=", "Interest recorded." in interest_body)

if 'href="/interest.html"' not in root_body:
    raise SystemExit("V65_88A_FAIL=live_cta_missing")
if "Interest recorded." not in interest_body:
    raise SystemExit("V65_88A_FAIL=live_interest_page_missing")

tracking = {
    "schema": "companyos.live_validation_tracking.v1",
    "timestamp_unix": time.time(),
    "candidate_name": candidate_name,
    "project_name": project_name,
    "stable_public_url": stable_url,
    "conversion_url": stable_url.rstrip("/") + "/interest.html",
    "deployment_id": receipt.get("deployment_id"),
    "deployment_url": receipt.get("url"),
    "cta_installed": True,
    "analytics_enabled": False,
    "analytics_blocker": "cloudflare_api_token_missing_account_settings_permissions",
    "required_cloudflare_permissions": [
        "Account Settings Read",
        "Account Settings Write"
    ],
    "conversion_definition_after_analytics_enabled": "interest page views divided by landing page views",
    "financial_actions": False,
    "outreach": False,
    "wallet_signing": False,
    "domain_purchase": False,
}

tracking_path = LOCAL_RT / "live_validation_tracking.json"
tracking_path.write_text(json.dumps(tracking, indent=2, sort_keys=True) + "\n")

report = REPORT_DIR / f"v65_88a_cta_fallback_{int(time.time())}.json"
report.write_text(json.dumps(tracking, indent=2, sort_keys=True) + "\n")

print("PUBLIC_URL=", stable_url)
print("CONVERSION_URL=", stable_url.rstrip("/") + "/interest.html")
print("TRACKING_CONFIG=", tracking_path)
print("REPORT=", report)
print("ANALYTICS_STATUS=AWAITING_CLOUDFLARE_WEB_ANALYTICS_ENABLE")
print("V65_88A_CTA_INSTALL=PASS")
print("V65_88A_LIVE_REDEPLOY=PASS")
print("V65_88A_ROOT_REACHABILITY=PASS")
print("V65_88A_CONVERSION_PAGE_REACHABILITY=PASS")
print("V65_88A_COMPLETE")
PY
