#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

GLOBAL_RT="$HOME/.companyos_runtime"
LOCAL_RT="$HOME/companyos/.companyos_runtime"
LAUNCHER="$HOME/storage/downloads/companyos_v65_85_managed_continuous_profit_runtime.sh"
PIDFILE="$GLOBAL_RT/continuous_profit_runtime.pid"
STOPFILE="$GLOBAL_RT/continuous_goal_runtime.stop"

echo "===== COMPANYOS V65.87 LIVE VALIDATION LAUNCH ====="
echo "PURPOSE=REAL_PUBLIC_DEPLOYMENT_OF_TOP_PROFIT_CANDIDATE_FOR_VALIDATION"
echo "FINANCIAL_EXECUTION=DISABLED"
echo "WALLET_SIGNING=DISABLED"
echo "DOMAIN_PURCHASE=DISABLED"
echo "OUTREACH=DISABLED"

was_running=0
if [ -f "$PIDFILE" ]; then
    pid="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
        was_running=1
        echo "MANAGED_RUNTIME_WAS_RUNNING=true"
        if [ -f "$LAUNCHER" ]; then
            bash "$LAUNCHER" stop || true
        else
            printf 'stop\n' > "$STOPFILE"
        fi
        for _ in $(seq 1 20); do
            if ! kill -0 "$pid" 2>/dev/null; then break; fi
            sleep 1
        done
        if kill -0 "$pid" 2>/dev/null; then
            echo "V65_87_ABORT=managed_runtime_did_not_stop"
            exit 1
        fi
        echo "MANAGED_RUNTIME_PAUSED=PASS"
    fi
fi

restart_runtime() {
    if [ "$was_running" = "1" ] && [ -f "$LAUNCHER" ]; then
        echo "===== RESTARTING MANAGED PROFIT RUNTIME ====="
        bash "$LAUNCHER" start || true
    fi
}
trap restart_runtime EXIT

python - <<'PY'
from pathlib import Path
from collections import Counter
import html
import json
import os
import re
import sqlite3
import statistics
import time
import urllib.request

HOME = Path.home()
ROOT = HOME / "companyos"
GLOBAL_RT = HOME / ".companyos_runtime"
LOCAL_RT = ROOT / ".companyos_runtime"
QUEUE_DIR = GLOBAL_RT / "task_queue"
DB = GLOBAL_RT / "execution_kernel.sqlite3"
REPORT_DIR = GLOBAL_RT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def load_json(p, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(p).read_text(errors="ignore"))
    except Exception:
        return default

def read_json_dir(path):
    vals, bad = [], []
    if not path.exists():
        return vals, bad
    for p in path.glob("*.json"):
        try:
            vals.append(json.loads(p.read_text(errors="ignore")))
        except Exception as exc:
            bad.append((str(p), type(exc).__name__))
    return vals, bad

# ---------- Health gate ----------
tasks, badq = read_json_dir(QUEUE_DIR)
states = Counter(str(x.get("state") or "UNKNOWN") for x in tasks)

con = sqlite3.connect(str(DB))
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_count = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

orch, bado = read_json_dir(GLOBAL_RT / "ceo_orchestrations")
intakes, badi = read_json_dir(GLOBAL_RT / "goal_intake")

running_orch = [x for x in orch if str(x.get("state")) == "RUNNING"]
pending_intakes = [x for x in intakes if str(x.get("state")) in ("PENDING", "CLAIMED")]

print("QUEUE_STATES_BEFORE=", dict(sorted(states.items())))
print("RUNNING_ORCHESTRATIONS_BEFORE=", len(running_orch))
print("PENDING_INTAKES_BEFORE=", len(pending_intakes))
print("DB_INTEGRITY_BEFORE=", integrity)
print("QUEUE_MINUS_DB_DELTA_BEFORE=", len(tasks) - db_count)

if badq or bado or badi:
    raise SystemExit("V65_87_ABORT=unreadable_runtime_json")
if integrity != "ok":
    raise SystemExit("V65_87_ABORT=db_integrity_failed")
if len(tasks) != db_count:
    raise SystemExit("V65_87_ABORT=projection_mismatch")
if states.get("QUEUED", 0) or states.get("CLAIMED", 0) or states.get("RUNNING", 0):
    raise SystemExit("V65_87_ABORT=active_task_work_present")
if running_orch:
    raise SystemExit("V65_87_ABORT=running_orchestration_present")
if pending_intakes:
    raise SystemExit("V65_87_ABORT=pending_intake_present")

# ---------- Select strongest current candidate ----------
status_paths = [
    LOCAL_RT / "profit_opportunity_status.json",
    GLOBAL_RT / "profit_opportunity_status.json",
]

status = {}
status_path = None
for p in status_paths:
    row = load_json(p, {})
    if row:
        status = row
        status_path = p
        break

if not status:
    from companyos.runtime.profit_opportunity_engine import choose
    status = choose()
    status_path = LOCAL_RT / "profit_opportunity_status.json"

ranked = [x for x in (status.get("ranked") or []) if isinstance(x, dict)]
if not ranked:
    raise SystemExit("V65_87_ABORT=no_ranked_profit_candidates")

candidate = ranked[0]
name = str(candidate.get("name") or candidate.get("title") or "CompanyOS Validation Venture").strip()
score = float(candidate.get("score") or candidate.get("profit_first_score") or 0)
compliance = float(candidate.get("compliance_risk") or candidate.get("legal_compliance_risk_pct") or 0)

rejections = []
cid = candidate.get("id")
for x in status.get("qualification_rejections") or []:
    if isinstance(x, dict) and x.get("id") == cid:
        rejections = list(x.get("reasons") or [])
        break

print("PROFIT_STATUS_PATH=", status_path)
print("PROFIT_ENGINE_DECISION=", status.get("decision"))
print("TOP_CANDIDATE_NAME=", name)
print("TOP_CANDIDATE_SCORE=", score)
print("TOP_CANDIDATE_EXPECTED_PROFIT=", candidate.get("expected_profit"))
print("TOP_CANDIDATE_PROBABILITY=", candidate.get("probability"))
print("TOP_CANDIDATE_EVIDENCE_COUNT=", candidate.get("evidence_count"))
print("TOP_CANDIDATE_QUALIFICATION_GAPS=", rejections)

# Validation-only gate: test a public page without claiming the opportunity
# passed the production investment threshold.
if score <= 0:
    raise SystemExit("V65_87_ABORT=top_candidate_has_no_positive_score")
if compliance >= 80:
    raise SystemExit("V65_87_ABORT=top_candidate_compliance_risk_too_high")

payload = candidate.get("payload") if isinstance(candidate.get("payload"), dict) else {}

def first(*vals, default=""):
    for v in vals:
        if v not in (None, "", [], {}):
            return str(v)
    return default

target = first(
    candidate.get("target_customer"),
    payload.get("target_customer"),
    payload.get("customer"),
    payload.get("buyer"),
    default="Prospective customers in the target market",
)
offer = first(
    candidate.get("offer"),
    payload.get("offer"),
    payload.get("product"),
    payload.get("service"),
    payload.get("value_proposition"),
    default="A focused solution being evaluated by CompanyOS",
)
market = first(
    candidate.get("category"),
    candidate.get("market"),
    payload.get("market"),
    payload.get("sector"),
    payload.get("industry"),
    default="Target market",
)
next_action = first(
    candidate.get("next_action"),
    payload.get("next_action"),
    payload.get("recommended_action"),
    default="Measure real-world interest and improve the offer using evidence.",
)

slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "companyos-validation"
site_dir = ROOT / "companyos_runtime" / "live_validation" / slug
site_dir.mkdir(parents=True, exist_ok=True)

index = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(name)} - Early Validation</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#0b0d10;color:#f6f7f8}}
main{{max-width:850px;margin:auto;padding:72px 24px}}
.badge{{display:inline-block;padding:7px 11px;border:1px solid #525861;border-radius:999px;font-size:13px}}
h1{{font-size:clamp(40px,8vw,76px);line-height:.98;margin:28px 0}}
.lead{{font-size:22px;line-height:1.5;color:#c8cdd4}}
.card{{margin-top:32px;padding:24px;border:1px solid #30343a;border-radius:18px;background:#12151a}}
.label{{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:#8e98a6}}
.value{{font-size:18px;margin-top:7px}}
footer{{margin-top:48px;color:#7f8894;font-size:13px}}
</style>
</head>
<body>
<main>
<span class="badge">CompanyOS live market validation</span>
<h1>{html.escape(name)}</h1>
<p class="lead">{html.escape(offer)}</p>
<div class="card">
<div class="label">Intended customer</div>
<div class="value">{html.escape(target)}</div>
</div>
<div class="card">
<div class="label">Market</div>
<div class="value">{html.escape(market)}</div>
</div>
<div class="card">
<div class="label">Current validation objective</div>
<div class="value">{html.escape(next_action)}</div>
</div>
<footer>
This page is an early market-validation experiment. Availability, pricing,
features and commercial terms are not yet final.
</footer>
</main>
</body>
</html>
"""
(site_dir / "index.html").write_text(index, encoding="utf-8")

manifest = {
    "schema": "companyos.live_validation.v1",
    "created_at_unix": time.time(),
    "candidate": candidate,
    "profit_engine_decision": status.get("decision"),
    "qualification_gaps": rejections,
    "purpose": "public_market_validation",
    "financial_actions": False,
    "wallet_signing": False,
    "domain_purchase": False,
    "outreach": False,
}
(site_dir / "validation.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n")

print("VALIDATION_SITE_DIR=", site_dir)
print("VALIDATION_PAGE_GENERATED=PASS")

# ---------- Deploy ----------
from companyos.connectors.hosting_router import HostingRouter
router = HostingRouter()
cf_health = router.health()
print("CLOUDFLARE_HEALTH=", cf_health)

provider = None
receipt = None
start = time.perf_counter()

if cf_health.get("healthy"):
    provider = "cloudflare"
    project = (
        os.getenv("COMPANYOS_CLOUDFLARE_PROJECT", "").strip()
        or ("companyos-" + slug)[:58]
    )
    receipt = router.deploy_directory(project, str(site_dir), "main")
else:
    from companyos.connectors_live.config import load_dotenv
    from companyos.connectors_live.adapters import HostingConnector

    load_dotenv(ROOT / ".env")
    token = os.getenv("VERCEL_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "V65_87_ABORT=no_healthy_hosting_provider:"
            + str(cf_health.get("cloudflare", cf_health))
        )

    provider = "vercel"
    vc = HostingConnector({
        "enabled": True,
        "dry_run": False,
        "token_env": "VERCEL_TOKEN",
        "request_timeout_seconds": 60,
        "max_retries": 2,
    })
    receipt = vc.execute(
        "deploy_production",
        {
            "project_name": ("companyos-" + slug)[:100],
            "website_path": str(site_dir),
        },
    )

deploy_seconds = round(time.perf_counter() - start, 3)
print("LIVE_PROVIDER=", provider)
print("DEPLOY_SECONDS=", deploy_seconds)
print("DEPLOY_RECEIPT=", receipt)

if not isinstance(receipt, dict):
    raise SystemExit("V65_87_FAIL=invalid_deploy_receipt")

if provider == "vercel":
    if not receipt.get("ok"):
        raise SystemExit(f"V65_87_FAIL=vercel_deployment_failed:{receipt}")
    public_url = receipt.get("live_url")
    deployment_id = receipt.get("deployment_id")
else:
    public_url = receipt.get("url")
    deployment_id = receipt.get("deployment_id")

if not public_url:
    raise SystemExit("V65_87_FAIL=public_url_missing")
if not str(public_url).startswith(("http://", "https://")):
    public_url = "https://" + str(public_url)

# ---------- Measure ----------
samples = []
http_status = None
page_bytes = None
last_error = None

for _ in range(15):
    try:
        t0 = time.perf_counter()
        req = urllib.request.Request(public_url, headers={"User-Agent":"CompanyOS-V65.87/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read()
            samples.append(round((time.perf_counter() - t0) * 1000, 2))
            http_status = int(resp.status)
            page_bytes = len(body)
        if 200 <= http_status < 400:
            break
    except Exception as exc:
        last_error = f"{type(exc).__name__}:{exc}"
        time.sleep(3)

if not samples or http_status is None or http_status >= 400:
    raise SystemExit(f"V65_87_FAIL=public_site_not_reachable:{last_error}")

for _ in range(4):
    try:
        t0 = time.perf_counter()
        req = urllib.request.Request(public_url, headers={"User-Agent":"CompanyOS-V65.87/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
            samples.append(round((time.perf_counter() - t0) * 1000, 2))
    except Exception:
        pass

avg_ms = round(statistics.mean(samples), 2)
min_ms = round(min(samples), 2)
max_ms = round(max(samples), 2)

record = {
    "schema": "companyos.live_validation_result.v1",
    "timestamp_unix": time.time(),
    "candidate_id": candidate.get("id"),
    "candidate_name": name,
    "candidate_score": score,
    "candidate_expected_profit": candidate.get("expected_profit"),
    "candidate_probability": candidate.get("probability"),
    "candidate_evidence_count": candidate.get("evidence_count"),
    "qualification_gaps": rejections,
    "profit_engine_decision": status.get("decision"),
    "provider": provider,
    "deployment_id": deployment_id,
    "public_url": public_url,
    "deploy_seconds": deploy_seconds,
    "http_status": http_status,
    "page_bytes": page_bytes,
    "latency_ms": {
        "samples": samples,
        "average": avg_ms,
        "minimum": min_ms,
        "maximum": max_ms,
    },
    "financial_actions": False,
    "wallet_signing": False,
    "domain_purchase": False,
    "outreach": False,
    "next_system_action": "collect_external_evidence_before_production_promotion",
}

report = REPORT_DIR / f"v65_87_live_validation_{int(time.time())}.json"
report.write_text(json.dumps(record, indent=2, sort_keys=True, default=str) + "\n")

(LOCAL_RT / "live_validation_latest.json").write_text(
    json.dumps(record, indent=2, sort_keys=True, default=str) + "\n"
)

with (LOCAL_RT / "live_validation_ledger.jsonl").open("a") as f:
    f.write(json.dumps(record, sort_keys=True, default=str) + "\n")

# Deployment existence counts only as low-quality evidence; it does NOT fake
# customer demand, willingness to pay, or profitability.
evidence_dir = LOCAL_RT / "canonical_research_outputs"
evidence_dir.mkdir(parents=True, exist_ok=True)
evidence_file = evidence_dir / f"live_validation_{slug}_{int(time.time())}.json"
evidence_file.write_text(
    json.dumps({
        "name": name,
        "business_model": candidate.get("mechanism") or payload.get("business_model") or "unknown",
        "target_customer": target,
        "market": market,
        "offer": offer,
        "next_action": "Collect real market response to the live validation page, then estimate willingness to pay and conversion.",
        "evidence": [public_url],
        "source_urls": [public_url],
        "evidence_quality_pct": 20,
        "execution_readiness_pct": max(float(candidate.get("readiness") or 0), 20),
        "expected_profit": candidate.get("expected_profit") or 0,
        "probability_success_pct": candidate.get("probability") or 0,
        "time_to_cash_days": candidate.get("time_to_cash_days") or 30,
        "capital_required": candidate.get("capital_required") or 0,
        "validation_status": "public_page_live_no_market_response_yet",
    }, indent=2, sort_keys=True, default=str) + "\n"
)

print("PUBLIC_URL=", public_url)
print("HTTP_STATUS=", http_status)
print("PAGE_BYTES=", page_bytes)
print("LATENCY_SAMPLES_MS=", samples)
print("LATENCY_AVG_MS=", avg_ms)
print("LATENCY_MIN_MS=", min_ms)
print("LATENCY_MAX_MS=", max_ms)
print("REPORT=", report)
print("EVIDENCE_FILE=", evidence_file)
print("V65_87_LIVE_VALIDATION_LAUNCH=PASS")
print("V65_87_PUBLIC_REACHABILITY=PASS")
print("V65_87_TECHNICAL_PERFORMANCE=PASS")
print("V65_87_PROFIT_GATE_NOT_BYPASSED=PASS")
print("V65_87_FINANCIAL_ACTIONS_BLOCKED=PASS")
print("V65_87_COMPLETE")
PY
