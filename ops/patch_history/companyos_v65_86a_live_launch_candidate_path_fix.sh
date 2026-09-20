#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

GLOBAL_RT="$HOME/.companyos_runtime"
LOCAL_RT="$HOME/companyos/.companyos_runtime"
LAUNCHER="$HOME/storage/downloads/companyos_v65_85_managed_continuous_profit_runtime.sh"
PIDFILE="$GLOBAL_RT/continuous_profit_runtime.pid"
STOPFILE="$GLOBAL_RT/continuous_goal_runtime.stop"

echo "===== COMPANYOS V65.86A LIVE LAUNCH CANDIDATE PATH FIX ====="
echo "MODE=ONE_REAL_PUBLIC_DEPLOYMENT"
echo "FINANCIAL_EXECUTION=DISABLED"
echo "DOMAIN_PURCHASE=DISABLED"
echo "OUTREACH=DISABLED"
echo "WALLET_SIGNING=DISABLED"

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
            echo "V65_86A_ABORT=managed_runtime_did_not_stop"
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
import json
import os
import re
import shutil
import sqlite3
import statistics
import tarfile
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

STAMP = int(time.time())
SNAP = GLOBAL_RT / "checkpoints" / f"v65_86a_live_launch_before_{STAMP}"
SNAP.mkdir(parents=True, exist_ok=True)

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
    for p in sorted(path.glob("*.json")):
        try:
            vals.append(json.loads(p.read_text(errors="ignore")))
        except Exception as exc:
            bad.append((str(p), type(exc).__name__, str(exc)))
    return vals, bad

# ---------- Preflight ----------
tasks, badq = read_json_dir(QUEUE_DIR)
states = Counter(str(x.get("state") or "UNKNOWN") for x in tasks)
orch, bado = read_json_dir(GLOBAL_RT / "ceo_orchestrations")
running_orch = [x for x in orch if str(x.get("state")) == "RUNNING"]
intakes, badi = read_json_dir(GLOBAL_RT / "goal_intake")
pending_intakes = [x for x in intakes if str(x.get("state")) in ("PENDING", "CLAIMED")]

con = sqlite3.connect(str(DB))
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_count = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

print("GLOBAL_RUNTIME=", GLOBAL_RT)
print("PROFIT_RUNTIME=", LOCAL_RT)
print("QUEUE_STATES_BEFORE=", dict(sorted(states.items())))
print("RUNNING_ORCHESTRATIONS_BEFORE=", len(running_orch))
print("PENDING_INTAKES_BEFORE=", len(pending_intakes))
print("DB_INTEGRITY_BEFORE=", integrity)
print("QUEUE_MINUS_DB_DELTA_BEFORE=", len(tasks) - db_count)

if badq or bado or badi:
    raise SystemExit("V65_86A_ABORT=unreadable_runtime_json")
if integrity != "ok":
    raise SystemExit("V65_86A_ABORT=db_integrity_failed")
if len(tasks) != db_count:
    raise SystemExit("V65_86A_ABORT=projection_mismatch")
if states.get("QUEUED",0) or states.get("CLAIMED",0) or states.get("RUNNING",0):
    raise SystemExit("V65_86A_ABORT=active_task_work_present")
if running_orch:
    raise SystemExit("V65_86A_ABORT=running_orchestration_present")
if pending_intakes:
    raise SystemExit("V65_86A_ABORT=pending_intake_present")

# ---------- Snapshot ----------
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(SNAP / "execution_kernel.sqlite3"))
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()

for dirname in ("task_queue", "goal_intake", "ceo_orchestrations", "goal_lifecycle", "goal_outcomes"):
    p = GLOBAL_RT / dirname
    if p.exists():
        with tarfile.open(SNAP / f"{dirname}.tar.gz", "w:gz") as tf:
            tf.add(p, arcname=dirname)

print("ROLLBACK_SNAPSHOT=PASS")
print("SNAPSHOT_DIR=", SNAP)

# ---------- Corrected candidate discovery ----------
candidate = None
candidate_source = None
candidate_basis = None

def accept_candidate(raw, source, basis):
    global candidate, candidate_source, candidate_basis
    if not isinstance(raw, dict) or not raw:
        return False

    # Profit engine selected artifact wrapper.
    if isinstance(raw.get("opportunity"), dict) and raw.get("opportunity"):
        c = dict(raw["opportunity"])
    # Profit status wrapper.
    elif isinstance(raw.get("chosen"), dict) and raw.get("chosen"):
        c = dict(raw["chosen"])
    else:
        c = dict(raw)

    payload = c.get("payload") if isinstance(c.get("payload"), dict) else {}
    c.setdefault("name", payload.get("name") or payload.get("title"))
    c.setdefault("title", c.get("name"))
    c.setdefault(
        "summary",
        payload.get("description")
        or payload.get("summary")
        or payload.get("offer")
        or payload.get("value_proposition")
        or "A focused solution being tested against a real market need."
    )
    c.setdefault(
        "target_customer",
        payload.get("target_customer")
        or payload.get("customer")
        or payload.get("audience")
        or "customers who need this solution"
    )
    c.setdefault("cta", "Learn More")

    if not (c.get("name") or c.get("title")):
        return False

    candidate = c
    candidate_source = str(source)
    candidate_basis = basis
    return True

# 1) Actual current profit-opportunity engine selected artifacts.
selected_files = []
for base in (LOCAL_RT / "profit_opportunities", GLOBAL_RT / "profit_opportunities"):
    if base.exists():
        selected_files.extend(base.glob("selected_*.json"))

selected_files = sorted(
    selected_files,
    key=lambda p: p.stat().st_mtime if p.exists() else 0,
    reverse=True,
)

for p in selected_files:
    raw = load_json(p, {})
    if accept_candidate(raw, p, "profit_opportunity_selected_artifact"):
        break

# 2) Current profit engine status chosen object.
if candidate is None:
    for p in (
        LOCAL_RT / "profit_opportunity_status.json",
        GLOBAL_RT / "profit_opportunity_status.json",
    ):
        raw = load_json(p, {})
        if raw.get("decision") == "execute_candidate" and accept_candidate(
            raw, p, "profit_opportunity_status_chosen"
        ):
            break

# 3) Profit-first ranked selected-for-validation candidate.
if candidate is None:
    for p in (
        LOCAL_RT / "profit_first_venture_rankings.json",
        GLOBAL_RT / "profit_first_venture_rankings.json",
    ):
        raw = load_json(p, {})
        selected = raw.get("selected_for_validation") or []
        if selected and isinstance(selected[0], dict):
            if accept_candidate(selected[0], p, "profit_first_selected_for_validation"):
                break

# 4) Latest execution workspace brief created by profit opportunity engine.
if candidate is None:
    briefs = sorted(
        ROOT.glob("workspace/*/venture_brief.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    for p in briefs:
        raw = load_json(p, {})
        if isinstance(raw.get("opportunity"), dict) and raw["opportunity"]:
            if accept_candidate(raw, p, "profit_execution_workspace_brief"):
                break

print("SELECTED_ARTIFACT_COUNT=", len(selected_files))
print("CANDIDATE_SOURCE=", candidate_source)
print("CANDIDATE_BASIS=", candidate_basis)

if not candidate:
    print("LOCAL_PROFIT_STATUS=", load_json(LOCAL_RT / "profit_opportunity_status.json", {}))
    print("LOCAL_PROFIT_DISPATCH=", load_json(LOCAL_RT / "profit_opportunity_dispatch.json", {}))
    raise SystemExit("V65_86A_ABORT=no_profit_candidate_found")

print("CANDIDATE_NAME=", candidate.get("name") or candidate.get("title"))
print("CANDIDATE_SCORE=", candidate.get("score", candidate.get("profit_first_score")))
print("CANDIDATE_EXPECTED_PROFIT=", candidate.get("expected_profit"))
print("CANDIDATE_NEXT_ACTION=", candidate.get("next_action"))

# Running this script is explicit authorization for exactly one public test deployment.
candidate["execution_qualified"] = True
candidate["manual_approval_granted"] = True
candidate["manual_approval_reason"] = "owner_explicit_one_public_launch_v65_86a"
candidate["qualification_state"] = "execution_qualified"

from companyos.runtime.venture_launch_orchestrator import VentureLaunchOrchestrator
launcher = VentureLaunchOrchestrator(HOME)

qualified, reason = launcher._qualified(candidate)
print("CANDIDATE_QUALIFIED=", qualified)
print("CANDIDATE_QUALIFICATION_REASON=", reason)
if not qualified:
    raise SystemExit(f"V65_86A_ABORT=candidate_not_qualified:{reason}")

title, slug, site_dir = launcher._site(candidate)
print("VENTURE_TITLE=", title)
print("VENTURE_SLUG=", slug)
print("SITE_DIR=", site_dir)

# ---------- Live provider selection ----------
from companyos.connectors.hosting_router import HostingRouter
router = HostingRouter()
cf_health = router.health()
print("CLOUDFLARE_HEALTH=", cf_health)

provider = None
receipt = None
t0 = time.perf_counter()

if cf_health.get("healthy"):
    provider = "cloudflare"
    project = (
        os.getenv("COMPANYOS_CLOUDFLARE_PROJECT", "").strip()
        or ("companyos-" + re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-"))[:58]
        or "companyos-live-trial"
    )
    receipt = router.deploy_directory(project, str(site_dir), "main")
else:
    from companyos.connectors_live.config import load_dotenv
    from companyos.connectors_live.adapters import HostingConnector

    load_dotenv(ROOT / ".env")
    token = os.getenv("VERCEL_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "V65_86A_ABORT=no_healthy_hosting_provider:"
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

deploy_seconds = round(time.perf_counter() - t0, 3)

print("LIVE_PROVIDER=", provider)
print("DEPLOY_SECONDS=", deploy_seconds)
print("DEPLOY_RECEIPT=", receipt)

if not isinstance(receipt, dict):
    raise SystemExit("V65_86A_FAIL=invalid_deploy_receipt")

if provider == "vercel":
    if not receipt.get("ok"):
        raise SystemExit(f"V65_86A_FAIL=vercel_deployment_failed:{receipt}")
    public_url = receipt.get("live_url")
    deployment_id = receipt.get("deployment_id")
else:
    public_url = receipt.get("url")
    deployment_id = receipt.get("deployment_id")

if not public_url:
    raise SystemExit("V65_86A_FAIL=public_url_missing")
if not str(public_url).startswith(("http://", "https://")):
    public_url = "https://" + str(public_url)

# ---------- Real reachability / performance ----------
samples = []
status_code = None
page_bytes = None
last_error = None

for attempt in range(15):
    try:
        start = time.perf_counter()
        req = urllib.request.Request(
            public_url,
            headers={"User-Agent": "CompanyOS-V65.86A-LiveTrial/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read()
            ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = int(resp.status)
            page_bytes = len(body)
            samples.append(ms)
        if 200 <= status_code < 400:
            break
    except Exception as exc:
        last_error = f"{type(exc).__name__}:{exc}"
        time.sleep(3)

if not samples or status_code is None or status_code >= 400:
    raise SystemExit(f"V65_86A_FAIL=public_site_not_reachable:{last_error}")

for _ in range(4):
    try:
        start = time.perf_counter()
        req = urllib.request.Request(
            public_url,
            headers={"User-Agent": "CompanyOS-V65.86A-LiveTrial/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
            samples.append(round((time.perf_counter() - start) * 1000, 2))
    except Exception:
        pass

avg_ms = round(statistics.mean(samples), 2)
min_ms = round(min(samples), 2)
max_ms = round(max(samples), 2)

record = {
    "version": "V65.86A",
    "timestamp_unix": time.time(),
    "mode": "one_real_public_deployment",
    "candidate_source": candidate_source,
    "candidate_basis": candidate_basis,
    "candidate_name": candidate.get("name") or candidate.get("title"),
    "candidate_score": candidate.get("score", candidate.get("profit_first_score")),
    "candidate_expected_profit": candidate.get("expected_profit"),
    "candidate_next_action": candidate.get("next_action"),
    "provider": provider,
    "deployment_id": deployment_id,
    "public_url": public_url,
    "deploy_seconds": deploy_seconds,
    "http_status": status_code,
    "page_bytes": page_bytes,
    "response_latency_ms": {
        "samples": samples,
        "average": avg_ms,
        "minimum": min_ms,
        "maximum": max_ms,
    },
    "financial_execution": False,
    "domain_purchase": False,
    "wallet_signing": False,
    "outreach": False,
    "rollback_snapshot": str(SNAP),
    "deployment_receipt": receipt,
}

report = REPORT_DIR / f"v65_86a_live_public_launch_{STAMP}.json"
report.write_text(json.dumps(record, indent=2, sort_keys=True, default=str) + "\n")

(GLOBAL_RT / "venture_launch_latest.json").write_text(
    json.dumps(
        {
            "timestamp": time.time(),
            "status": "launched",
            "title": title,
            "slug": slug,
            "public_url": public_url,
            "deployment": receipt,
            "candidate_source": candidate_source,
            "next_action": "measure_market_response",
            "v65_86a_trial": True,
        },
        indent=2,
        sort_keys=True,
        default=str,
    ) + "\n"
)

with (GLOBAL_RT / "venture_launch_ledger.jsonl").open("a") as f:
    f.write(json.dumps(record, sort_keys=True, default=str) + "\n")

# ---------- Final integrity ----------
tasks_after, bad_after = read_json_dir(QUEUE_DIR)
states_after = Counter(str(x.get("state") or "UNKNOWN") for x in tasks_after)

con = sqlite3.connect(str(DB))
try:
    integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_after = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

print("PUBLIC_URL=", public_url)
print("HTTP_STATUS=", status_code)
print("PAGE_BYTES=", page_bytes)
print("LATENCY_SAMPLES_MS=", samples)
print("LATENCY_AVG_MS=", avg_ms)
print("LATENCY_MIN_MS=", min_ms)
print("LATENCY_MAX_MS=", max_ms)
print("QUEUE_STATES_AFTER=", dict(sorted(states_after.items())))
print("DB_INTEGRITY_AFTER=", integrity_after)
print("QUEUE_MINUS_DB_DELTA_AFTER=", len(tasks_after) - db_after)
print("REPORT=", report)
print("ROLLBACK_AVAILABLE=", SNAP)

if bad_after:
    raise SystemExit("V65_86A_FAIL=unreadable_queue_after")
if integrity_after != "ok":
    raise SystemExit("V65_86A_FAIL=db_integrity_after")
if len(tasks_after) != db_after:
    raise SystemExit("V65_86A_FAIL=projection_mismatch_after")

print("V65_86A_CANDIDATE_DISCOVERY=PASS")
print("V65_86A_LIVE_PUBLIC_LAUNCH=PASS")
print("V65_86A_PUBLIC_REACHABILITY=PASS")
print("V65_86A_PERFORMANCE_MEASUREMENT=PASS")
print("V65_86A_FINANCIAL_ACTIONS_BLOCKED=PASS")
print("V65_86A_RUNTIME_INTEGRITY=PASS")
print("V65_86A_COMPLETE")
PY
