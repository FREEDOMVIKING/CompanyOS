#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.89 WEB ANALYTICS VERIFY ====="
echo "ACTION=VERIFY_CLOUDFLARE_WEB_ANALYTICS_BEACON"
echo "REDEPLOY=NO"
echo "FINANCIAL_ACTIONS=DISABLED"

python - <<'PY'
from pathlib import Path
import json
import time
import urllib.request

HOME = Path.home()
ROOT = HOME / "companyos"
LOCAL_RT = ROOT / ".companyos_runtime"
GLOBAL_RT = HOME / ".companyos_runtime"
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

base = (
    tracking.get("stable_public_url")
    or latest.get("public_url")
    or "https://companyos-regional-construction-ai.pages.dev"
)
base = str(base).rstrip("/")

root_url = base + "/"
interest_url = base + "/interest.html"

print("ROOT_URL=", root_url)
print("INTEREST_URL=", interest_url)

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CompanyOS-V65.89-AnalyticsVerify/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return int(resp.status), resp.read().decode("utf-8", "replace")

def has_beacon(body):
    return (
        "static.cloudflareinsights.com/beacon.min.js" in body
        or "data-cf-beacon" in body
        or "cloudflareinsights.com" in body
    )

deadline = time.time() + 180
root_status = interest_status = None
root_beacon = interest_beacon = False
last_error = None

while time.time() < deadline:
    try:
        root_status, root_body = fetch(root_url)
        interest_status, interest_body = fetch(interest_url)

        root_beacon = has_beacon(root_body)
        interest_beacon = has_beacon(interest_body)

        print("ROOT_HTTP_STATUS=", root_status)
        print("INTEREST_HTTP_STATUS=", interest_status)
        print("ROOT_ANALYTICS_BEACON=", root_beacon)
        print("INTEREST_ANALYTICS_BEACON=", interest_beacon)

        if root_status == 200 and interest_status == 200 and root_beacon and interest_beacon:
            break
    except Exception as exc:
        last_error = f"{type(exc).__name__}:{exc}"
        print("VERIFY_WAIT=", last_error)

    time.sleep(10)

enabled = bool(
    root_status == 200
    and interest_status == 200
    and root_beacon
    and interest_beacon
)

record = {
    "schema": "companyos.web_analytics_verify.v1",
    "timestamp_unix": time.time(),
    "stable_public_url": base,
    "root_url": root_url,
    "interest_url": interest_url,
    "root_http_status": root_status,
    "interest_http_status": interest_status,
    "root_beacon_present": root_beacon,
    "interest_beacon_present": interest_beacon,
    "analytics_enabled": enabled,
    "conversion_definition": "interest page views / landing page views",
    "last_error": last_error,
    "financial_actions": False,
}

report = REPORT_DIR / f"v65_89_web_analytics_verify_{int(time.time())}.json"
report.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

tracking.update({
    "analytics_enabled": enabled,
    "analytics_verified_at_unix": time.time(),
    "conversion_definition": "interest page views divided by landing page views",
})
(LOCAL_RT / "live_validation_tracking.json").write_text(
    json.dumps(tracking, indent=2, sort_keys=True) + "\n"
)

print("REPORT=", report)

if enabled:
    print("V65_89_ROOT_ANALYTICS=PASS")
    print("V65_89_INTEREST_ANALYTICS=PASS")
    print("V65_89_CONVERSION_MEASUREMENT_READY=PASS")
    print("V65_89_COMPLETE")
else:
    print("V65_89_ANALYTICS_NOT_YET_ENABLED")
    print("NEXT_STEP=Enable Cloudflare Web Analytics for the Pages project, then rerun this script.")
    raise SystemExit(2)
PY
