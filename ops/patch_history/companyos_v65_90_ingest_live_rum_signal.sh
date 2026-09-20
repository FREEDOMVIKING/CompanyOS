#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.90 LIVE RUM SIGNAL INGEST ====="
echo "PURPOSE=READ_REAL_CLOUDFLARE_WEB_ANALYTICS_WITHOUT_FAKING_MARKET_EVIDENCE"
echo "WRITE_PROFIT_DECISION=NO"
echo "FINANCIAL_ACTIONS=DISABLED"
echo "OUTREACH=DISABLED"
echo "WALLET_SIGNING=DISABLED"

python - <<'PY'
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import os
import re
import time
import urllib.request
import urllib.error

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

# Load .env if CompanyOS has one.
try:
    from companyos.connectors_live.config import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

tracking = load_json(LOCAL_RT / "live_validation_tracking.json", {})
latest = load_json(LOCAL_RT / "live_validation_latest.json", {})

base = str(
    tracking.get("stable_public_url")
    or latest.get("public_url")
    or "https://companyos-regional-construction-ai.pages.dev"
).rstrip("/")

host = re.sub(r"^https?://", "", base).split("/", 1)[0]
candidate_name = str(
    tracking.get("candidate_name")
    or latest.get("candidate_name")
    or "Regional Construction AI"
)

print("PUBLIC_URL=", base)
print("HOST=", host)
print("CANDIDATE_NAME=", candidate_name)

# Fetch browser-facing HTML and recover Cloudflare's injected site tag.
req = urllib.request.Request(
    base + "/",
    headers={"User-Agent":"CompanyOS-V65.90/1.0"},
)
with urllib.request.urlopen(req, timeout=20) as resp:
    html = resp.read().decode("utf-8", "replace")
    root_status = int(resp.status)

print("ROOT_HTTP_STATUS=", root_status)

patterns = [
    r'data-cf-beacon=["\'][^"\']*token[\\"]*:\s*[\\"]*([0-9a-fA-F]{16,64})',
    r'"token"\s*:\s*"([0-9a-fA-F]{16,64})"',
    r"'token'\s*:\s*'([0-9a-fA-F]{16,64})'",
]
site_tag = None
for pat in patterns:
    m = re.search(pat, html)
    if m:
        site_tag = m.group(1)
        break

# Cloudflare sometimes escapes JSON in the HTML attribute.
if not site_tag:
    m = re.search(r'data-cf-beacon=["\']([^"\']+)["\']', html)
    if m:
        raw = m.group(1).replace("&quot;", '"').replace("\\&quot;", '"')
        try:
            obj = json.loads(raw)
            site_tag = str(obj.get("token") or "").strip() or None
        except Exception:
            pass

print("SITE_TAG_PRESENT=", bool(site_tag))
if site_tag:
    print("SITE_TAG_PREFIX=", site_tag[:8] + "..." + site_tag[-4:])

if not site_tag:
    raise SystemExit("V65_90_ABORT=cloudflare_site_tag_not_found_in_live_html")

token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()

if not token or not account_id:
    raise SystemExit("V65_90_ABORT=cloudflare_credentials_missing")

end = datetime.now(timezone.utc)
start = end - timedelta(hours=24)
start_s = start.strftime("%Y-%m-%dT%H:%M:%SZ")
end_s = end.strftime("%Y-%m-%dT%H:%M:%SZ")

# Sanitize interpolated values before constructing the GraphQL query.
hex_re = re.compile(r"^[0-9a-fA-F]{16,64}$")
host_re = re.compile(r"^[A-Za-z0-9.-]+$")

if not hex_re.match(account_id):
    raise SystemExit("V65_90_ABORT=unexpected_account_id_format")
if not hex_re.match(site_tag):
    raise SystemExit("V65_90_ABORT=unexpected_site_tag_format")
if not host_re.match(host):
    raise SystemExit("V65_90_ABORT=unexpected_host_format")

query = f"""
query {{
  viewer {{
    accounts(filter: {{ accountTag: "{account_id}" }}) {{
      paths: rumPageloadEventsAdaptiveGroups(
        limit: 100
        orderBy: [count_DESC]
        filter: {{
          siteTag: "{site_tag}"
          requestHost: "{host}"
          datetime_geq: "{start_s}"
          datetime_leq: "{end_s}"
          bot: 0
        }}
      ) {{
        count
        avg {{
          sampleInterval
        }}
        sum {{
          visits
        }}
        dimensions {{
          requestPath
        }}
      }}
    }}
  }}
}}
"""

payload = json.dumps({"query": query}).encode("utf-8")
gql_req = urllib.request.Request(
    "https://api.cloudflare.com/client/v4/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CompanyOS-V65.90/1.0",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(gql_req, timeout=60) as resp:
        raw = resp.read().decode("utf-8", "replace")
        status = int(resp.status)
except urllib.error.HTTPError as exc:
    raw = exc.read().decode("utf-8", "replace")
    print("GRAPHQL_HTTP_STATUS=", exc.code)
    print("GRAPHQL_HTTP_ERROR=", raw[:1500])
    raise SystemExit("V65_90_ABORT=cloudflare_graphql_http_error")

print("GRAPHQL_HTTP_STATUS=", status)

try:
    obj = json.loads(raw)
except Exception:
    print("GRAPHQL_RAW=", raw[:1500])
    raise SystemExit("V65_90_ABORT=graphql_non_json_response")

if obj.get("errors"):
    print("GRAPHQL_ERRORS=", json.dumps(obj["errors"], sort_keys=True))
    messages = " | ".join(str(x.get("message") or "") for x in obj["errors"])
    if "permission" in messages.lower() or "auth" in messages.lower() or "access" in messages.lower():
        print("REQUIRED_TOKEN_PERMISSION=Account Analytics Read")
        raise SystemExit("V65_90_ABORT=cloudflare_token_missing_account_analytics_read")
    raise SystemExit("V65_90_ABORT=cloudflare_graphql_query_error")

accounts = (((obj.get("data") or {}).get("viewer") or {}).get("accounts") or [])
if not accounts:
    raise SystemExit("V65_90_ABORT=no_account_analytics_scope")

groups = accounts[0].get("paths") or []

rows = []
for g in groups:
    dims = g.get("dimensions") or {}
    avg = g.get("avg") or {}
    sums = g.get("sum") or {}
    rows.append({
        "path": str(dims.get("requestPath") or ""),
        "pageviews": int(g.get("count") or 0),
        "visits": float(sums.get("visits") or 0),
        "sample_interval": float(avg.get("sampleInterval") or 1),
    })

rows.sort(key=lambda x: x["pageviews"], reverse=True)

landing_views = sum(r["pageviews"] for r in rows if r["path"] in ("", "/"))
interest_views = sum(r["pageviews"] for r in rows if r["path"] in ("/interest.html", "/interest"))
total_pageviews = sum(r["pageviews"] for r in rows)

conversion_rate = None
if landing_views > 0:
    conversion_rate = round(interest_views / landing_views, 4)

sample_intervals = sorted({r["sample_interval"] for r in rows})
sampled = any(x > 1.0 for x in sample_intervals)

# Do NOT promote this into profit evidence yet. A tiny sample, especially if the
# owner is testing the site, is not reliable market proof.
if landing_views >= 20:
    evidence_state = "market_sample_started"
elif total_pageviews > 0:
    evidence_state = "insufficient_sample"
else:
    evidence_state = "no_rum_data_yet"

signal = {
    "schema": "companyos.live_market_signal.v1",
    "timestamp_unix": time.time(),
    "window": {
        "start_utc": start_s,
        "end_utc": end_s,
        "hours": 24,
    },
    "candidate_name": candidate_name,
    "public_url": base,
    "host": host,
    "site_tag_prefix": site_tag[:8],
    "total_pageviews": total_pageviews,
    "landing_pageviews": landing_views,
    "interest_pageviews": interest_views,
    "interest_conversion_rate": conversion_rate,
    "sample_intervals": sample_intervals,
    "sampled": sampled,
    "path_rows": rows,
    "evidence_state": evidence_state,
    "profit_engine_promotion": False,
    "reason_not_promoted": (
        "Market traffic is recorded, but CompanyOS will not treat this alone as proof "
        "of demand, willingness-to-pay, or profitability."
    ),
}

signal_path = LOCAL_RT / "live_market_signal_latest.json"
signal_path.write_text(json.dumps(signal, indent=2, sort_keys=True) + "\n")

ledger_path = LOCAL_RT / "live_market_signal_ledger.jsonl"
with ledger_path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(signal, sort_keys=True) + "\n")

report = REPORT_DIR / f"v65_90_live_rum_signal_{int(time.time())}.json"
report.write_text(json.dumps(signal, indent=2, sort_keys=True) + "\n")

print("ANALYTICS_WINDOW_START=", start_s)
print("ANALYTICS_WINDOW_END=", end_s)
print("PATH_ROWS=", json.dumps(rows, sort_keys=True))
print("TOTAL_PAGEVIEWS=", total_pageviews)
print("LANDING_PAGEVIEWS=", landing_views)
print("INTEREST_PAGEVIEWS=", interest_views)
print("INTEREST_CONVERSION_RATE=", conversion_rate)
print("SAMPLED=", sampled)
print("SAMPLE_INTERVALS=", sample_intervals)
print("EVIDENCE_STATE=", evidence_state)
print("SIGNAL_FILE=", signal_path)
print("REPORT=", report)

print("V65_90_GRAPHQL_ANALYTICS_READ=PASS")
print("V65_90_RUM_DATA_INGEST=PASS")
print("V65_90_NO_FAKE_PROFIT_PROMOTION=PASS")
print("V65_90_COMPLETE")
PY
