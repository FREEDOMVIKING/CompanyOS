#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.88 LIVE CONVERSION INSTRUMENTATION ====="
echo "PURPOSE=TRACK_REAL_PAGEVIEWS_AND_CTA_INTEREST"
echo "FINANCIAL_ACTIONS=DISABLED"
echo "OUTREACH=DISABLED"
echo "WALLET_SIGNING=DISABLED"
echo "DOMAIN_PURCHASE=DISABLED"

python - <<'PY'
from pathlib import Path
import json
import re
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
    raise SystemExit("V65_88_ABORT=live_validation_latest_missing")

public_url = str(latest.get("public_url") or "").strip()
candidate_name = str(
    latest.get("candidate_name")
    or latest.get("venture_title")
    or "Regional Construction AI"
).strip()

if not public_url:
    raise SystemExit("V65_88_ABORT=public_url_missing")

parsed = urllib.parse.urlparse(public_url)
hostname = parsed.netloc or parsed.path.split("/")[0]
if not hostname:
    raise SystemExit("V65_88_ABORT=hostname_missing")

slug = re.sub(r"[^a-z0-9]+", "-", candidate_name.lower()).strip("-")[:60]
if not slug:
    slug = "regional-construction-ai"

site_dir_candidates = [
    ROOT / "companyos_runtime" / "live_validation" / slug,
    ROOT / "companyos_runtime" / "live_validation" / "regional-construction-ai",
]
site_dir = next((p for p in site_dir_candidates if (p / "index.html").exists()), None)
if site_dir is None:
    raise SystemExit("V65_88_ABORT=live_site_source_not_found")

index_path = site_dir / "index.html"
interest_path = site_dir / "interest.html"

print("PUBLIC_URL=", public_url)
print("HOSTNAME=", hostname)
print("CANDIDATE_NAME=", candidate_name)
print("SITE_DIR=", site_dir)

from companyos.connectors.cloudflare_hosting import CloudflareHosting

cf = CloudflareHosting()
if not cf.configured:
    raise SystemExit("V65_88_ABORT=cloudflare_not_configured")

projects = cf.list_projects()
project = None
for p in projects:
    domains = list(p.get("domains") or [])
    subdomain = str(p.get("subdomain") or "")
    if hostname == subdomain or hostname in domains:
        project = p
        break

project_name = (
    (project or {}).get("name")
    or ("companyos-" + re.sub(r"[^a-z0-9-]+", "-", slug).strip("-"))[:58]
)

print("PROJECT_NAME=", project_name)

# Cloudflare Web Analytics site.
rum_sites = []
try:
    obj = cf._request("GET", f"/accounts/{cf.account_id}/rum/site_info/list")
    rum_sites = obj.get("result") or []
    print("RUM_LIST=PASS")
except Exception as exc:
    print("RUM_LIST_ERROR=", type(exc).__name__, str(exc))

def site_matches(site):
    hosts = set()
    for rule in site.get("rules") or []:
        h = str(rule.get("host") or "").strip()
        if h:
            hosts.add(h)
    zn = str((site.get("ruleset") or {}).get("zone_name") or "").strip()
    if zn:
        hosts.add(zn)
    direct = str(site.get("host") or "").strip()
    if direct:
        hosts.add(direct)
    return hostname in hosts

rum_site = next((s for s in rum_sites if site_matches(s)), None)
created = False

if rum_site is None:
    try:
        obj = cf._request(
            "POST",
            f"/accounts/{cf.account_id}/rum/site_info",
            {"host": hostname, "auto_install": False},
        )
        rum_site = obj.get("result") or {}
        created = True
        print("RUM_CREATE=PASS")
    except Exception as exc:
        print("RUM_CREATE_ERROR=", type(exc).__name__, str(exc))
        print("RUM_REQUIRED_PERMISSION=Account Settings Write")
        raise SystemExit("V65_88_ABORT=rum_site_create_permission_or_api_failure")

site_token = str((rum_site or {}).get("site_token") or "").strip()
snippet = str((rum_site or {}).get("snippet") or "").strip()

if not snippet and site_token:
    snippet = (
        "<!-- Cloudflare Web Analytics -->"
        "<script type='module' "
        "src='https://static.cloudflareinsights.com/beacon.min.js' "
        f"data-cf-beacon='{{\"token\":\"{site_token}\"}}'></script>"
        "<!-- End Cloudflare Web Analytics -->"
    )

if not snippet:
    raise SystemExit("V65_88_ABORT=rum_snippet_missing")

print("RUM_SITE_CREATED=", created)
print("RUM_SITE_TAG=", rum_site.get("site_tag"))
print("RUM_SITE_TOKEN_PRESENT=", bool(site_token))

# Instrument root page.
page = index_path.read_text(encoding="utf-8")
page = re.sub(
    r"<!-- V65\.88 CTA BEGIN -->.*?<!-- V65\.88 CTA END -->",
    "",
    page,
    flags=re.S,
)
page = re.sub(
    r"<!-- Cloudflare Web Analytics -->.*?<!-- End Cloudflare Web Analytics -->",
    "",
    page,
    flags=re.S,
)

cta_block = r"""
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
    This click is used only as an aggregate market-interest signal for this early validation test.
  </p>
</div>
<!-- V65.88 CTA END -->
"""

if "</main>" not in page:
    raise SystemExit("V65_88_ABORT=index_main_anchor_missing")
page = page.replace("</main>", cta_block + "\n</main>", 1)

if "</body>" not in page:
    raise SystemExit("V65_88_ABORT=index_body_anchor_missing")
page = page.replace("</body>", snippet + "\n</body>", 1)
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
Your visit to this page counts as an aggregate signal that the
{candidate_name} concept is worth investigating further.
</p>
<p><a href="/">Back to the validation page</a></p>
</main>
{snippet}
</body>
</html>
"""
interest_path.write_text(interest_html, encoding="utf-8")

root_text = index_path.read_text(encoding="utf-8")
interest_text = interest_path.read_text(encoding="utf-8")
checks = {
    "root_has_cta": 'href="/interest.html"' in root_text,
    "root_has_beacon": "static.cloudflareinsights.com/beacon.min.js" in root_text,
    "interest_has_beacon": "static.cloudflareinsights.com/beacon.min.js" in interest_text,
    "interest_page_exists": interest_path.exists(),
}
print("STATIC_CHECKS=", checks)
if not all(checks.values()):
    raise SystemExit("V65_88_FAIL=static_instrumentation_check")

# Redeploy same project.
started = time.perf_counter()
receipt = cf.deploy_directory(project_name, str(site_dir), "main")
deploy_seconds = round(time.perf_counter() - started, 3)
print("DEPLOY_RECEIPT=", receipt)
print("DEPLOY_SECONDS=", deploy_seconds)

aliases = list(receipt.get("aliases") or [])
stable_url = public_url
for a in aliases:
    if project_name + ".pages.dev" in str(a):
        stable_url = str(a)
        break

if not stable_url.startswith(("http://", "https://")):
    stable_url = "https://" + stable_url

def probe(url, tries=15):
    err = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CompanyOS-V65.88/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8", "replace")
                if 200 <= int(resp.status) < 400:
                    return int(resp.status), body
        except Exception as exc:
            err = f"{type(exc).__name__}:{exc}"
            time.sleep(3)
    raise RuntimeError(err or "probe_failed")

root_status, root_body = probe(stable_url.rstrip("/") + "/")
interest_status, interest_body = probe(stable_url.rstrip("/") + "/interest.html")

print("ROOT_HTTP_STATUS=", root_status)
print("INTEREST_HTTP_STATUS=", interest_status)
print("LIVE_ROOT_HAS_BEACON=", "static.cloudflareinsights.com/beacon.min.js" in root_body)
print("LIVE_ROOT_HAS_CTA=", 'href="/interest.html"' in root_body)
print("LIVE_INTEREST_HAS_BEACON=", "static.cloudflareinsights.com/beacon.min.js" in interest_body)

if "static.cloudflareinsights.com/beacon.min.js" not in root_body:
    raise SystemExit("V65_88_FAIL=live_root_beacon_missing")
if 'href="/interest.html"' not in root_body:
    raise SystemExit("V65_88_FAIL=live_root_cta_missing")
if "static.cloudflareinsights.com/beacon.min.js" not in interest_body:
    raise SystemExit("V65_88_FAIL=live_interest_beacon_missing")

tracking = {
    "schema": "companyos.live_validation_tracking.v1",
    "timestamp_unix": time.time(),
    "candidate_name": candidate_name,
    "project_name": project_name,
    "stable_public_url": stable_url,
    "deployment_url": receipt.get("url"),
    "deployment_id": receipt.get("deployment_id"),
    "rum_site_tag": rum_site.get("site_tag"),
    "rum_site_token": site_token,
    "root_path": "/",
    "conversion_path": "/interest.html",
    "conversion_definition": "interest page views divided by landing page views",
    "financial_actions": False,
    "outreach": False,
    "wallet_signing": False,
    "domain_purchase": False,
}
tracking_path = LOCAL_RT / "live_validation_tracking.json"
tracking_path.write_text(json.dumps(tracking, indent=2, sort_keys=True) + "\n")

report = REPORT_DIR / f"v65_88_live_conversion_instrumentation_{int(time.time())}.json"
report.write_text(json.dumps(tracking, indent=2, sort_keys=True) + "\n")

print("PUBLIC_URL=", stable_url)
print("CONVERSION_URL=", stable_url.rstrip("/") + "/interest.html")
print("TRACKING_CONFIG=", tracking_path)
print("REPORT=", report)
print("V65_88_RUM_SITE=PASS")
print("V65_88_CTA_INSTRUMENTATION=PASS")
print("V65_88_LIVE_REDEPLOY=PASS")
print("V65_88_ROOT_REACHABILITY=PASS")
print("V65_88_CONVERSION_PAGE_REACHABILITY=PASS")
print("V65_88_COMPLETE")
PY
