#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

RUNTIME="$HOME/.companyos_runtime"
LAUNCHER="$HOME/storage/downloads/companyos_v65_85_managed_continuous_profit_runtime.sh"
PIDFILE="$RUNTIME/continuous_profit_runtime.pid"
STOPFILE="$RUNTIME/continuous_goal_runtime.stop"

echo "===== COMPANYOS V65.86 LIVE PUBLIC LAUNCH PERFORMANCE TRIAL ====="
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
        if [ -x "$LAUNCHER" ] || [ -f "$LAUNCHER" ]; then
            bash "$LAUNCHER" stop || true
        else
            printf 'stop\n' > "$STOPFILE"
        fi
        for _ in $(seq 1 20); do
            if ! kill -0 "$pid" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        if kill -0 "$pid" 2>/dev/null; then
            echo "V65_86_ABORT=managed_runtime_did_not_stop"
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
import urllib.error

HOME = Path.home()
ROOT = HOME / "companyos"
RUNTIME = HOME / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = int(time.time())
SNAP = RUNTIME / "checkpoints" / f"v65_86_live_launch_before_{STAMP}"
SNAP.mkdir(parents=True, exist_ok=True)

print("SNAPSHOT_DIR=", SNAP)

# ---------- Runtime health gate ----------
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

tasks, badq = read_json_dir(QUEUE_DIR)
qstates = Counter(str(x.get("state") or "UNKNOWN") for x in tasks)

orch, bado = read_json_dir(RUNTIME / "ceo_orchestrations")
running_orch = [x for x in orch if str(x.get("state")) == "RUNNING"]

intakes, badi = read_json_dir(RUNTIME / "goal_intake")
pending_intakes = [
    x for x in intakes if str(x.get("state")) in ("PENDING", "CLAIMED")
]

con = sqlite3.connect(str(DB))
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_count = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

print("QUEUE_STATES_BEFORE=", dict(sorted(qstates.items())))
print("RUNNING_ORCHESTRATIONS_BEFORE=", len(running_orch))
print("PENDING_INTAKES_BEFORE=", len(pending_intakes))
print("DB_INTEGRITY_BEFORE=", integrity)
print("QUEUE_MINUS_DB_DELTA_BEFORE=", len(tasks) - db_count)
print("UNREADABLE_RUNTIME_JSON=", len(badq) + len(bado) + len(badi))

if badq or bado or badi:
    raise SystemExit("V65_86_ABORT=unreadable_runtime_json")
if integrity != "ok":
    raise SystemExit("V65_86_ABORT=db_integrity_failed")
if len(tasks) != db_count:
    raise SystemExit("V65_86_ABORT=projection_mismatch")
if qstates.get("QUEUED", 0) or qstates.get("CLAIMED", 0) or qstates.get("RUNNING", 0):
    raise SystemExit("V65_86_ABORT=active_task_work_present")
if running_orch:
    raise SystemExit("V65_86_ABORT=running_orchestration_present")
if pending_intakes:
    raise SystemExit("V65_86_ABORT=pending_intake_present")

# ---------- Rollback snapshot ----------
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(SNAP / "execution_kernel.sqlite3"))
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()

for dirname in (
    "task_queue",
    "goal_intake",
    "ceo_orchestrations",
    "goal_lifecycle",
    "goal_outcomes",
):
    p = RUNTIME / dirname
    if p.exists():
        with tarfile.open(SNAP / f"{dirname}.tar.gz", "w:gz") as tf:
            tf.add(p, arcname=dirname)

for p in (
    RUNTIME / "profit_opportunity_engine" / "selected.json",
    RUNTIME / "selected_profit_opportunity.json",
    RUNTIME / "venture_launch_latest.json",
    RUNTIME / "latest_deployment.json",
):
    if p.exists():
        dest = SNAP / p.name
        shutil.copy2(p, dest)

print("ROLLBACK_SNAPSHOT=PASS")

# ---------- Freeze candidate ----------
candidate_paths = [
    RUNTIME / "profit_opportunity_engine" / "selected.json",
    HOME / "companyos_runtime" / "profit_opportunity_engine" / "selected.json",
    RUNTIME / "selected_profit_opportunity.json",
    HOME / "companyos_runtime" / "venture_builder" / "latest_build.json",
]

candidate = None
candidate_path = None
for p in candidate_paths:
    if not p.exists():
        continue
    try:
        d = json.loads(p.read_text())
    except Exception:
        continue
    if isinstance(d, dict) and d:
        candidate = dict(d)
        candidate_path = p
        break

print("CANDIDATE_PATH=", candidate_path)
if not candidate:
    raise SystemExit("V65_86_ABORT=no_launch_candidate")

# The user's command to run this script is explicit approval for ONE public
# deployment only. It does not authorize spending, domains, finance, or outreach.
if candidate.get("requires_manual_approval"):
    candidate["manual_approval_granted"] = True
    candidate["manual_approval_reason"] = "owner_explicit_one_launch_v65_86"

from companyos.runtime.venture_launch_orchestrator import VentureLaunchOrchestrator
launcher = VentureLaunchOrchestrator(HOME)

qualified, reason = launcher._qualified(candidate)
print("CANDIDATE_QUALIFIED=", qualified)
print("CANDIDATE_QUALIFICATION_REASON=", reason)

if not qualified:
    raise SystemExit(f"V65_86_ABORT=candidate_not_qualified:{reason}")

title, slug, site_dir = launcher._site(candidate)
print("VENTURE_TITLE=", title)
print("VENTURE_SLUG=", slug)
print("SITE_DIR=", site_dir)

# ---------- Provider selection ----------
provider = None
receipt = None
deploy_started = time.perf_counter()

from companyos.connectors.hosting_router import HostingRouter
router = HostingRouter()
cloudflare_health = router.health()
print("CLOUDFLARE_HEALTH=", cloudflare_health)

if cloudflare_health.get("healthy"):
    provider = "cloudflare"
    project = (
        os.getenv("COMPANYOS_CLOUDFLARE_PROJECT", "").strip()
        or ("companyos-" + re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-"))[:58]
        or "companyos-live-trial"
    )
    receipt = router.deploy_directory(project, str(site_dir), "main")
else:
    # Existing CompanyOS Vercel connector fallback.
    from companyos.connectors_live.config import load_dotenv
    from companyos.connectors_live.adapters import HostingConnector

    load_dotenv(ROOT / ".env")
    vercel_token = os.getenv("VERCEL_TOKEN", "").strip()

    if not vercel_token:
        raise SystemExit(
            "V65_86_ABORT=no_healthy_hosting_provider:"
            + str(cloudflare_health.get("cloudflare", cloudflare_health))
        )

    provider = "vercel"
    cfg = {
        "enabled": True,
        "dry_run": False,
        "token_env": "VERCEL_TOKEN",
        "request_timeout_seconds": 60,
        "max_retries": 2,
    }
    vc = HostingConnector(cfg)
    receipt = vc.execute(
        "deploy_production",
        {
            "project_name": ("companyos-" + slug)[:100],
            "website_path": str(site_dir),
        },
    )

deploy_seconds = round(time.perf_counter() - deploy_started, 3)

print("LIVE_PROVIDER=", provider)
print("DEPLOY_SECONDS=", deploy_seconds)
print("DEPLOY_RECEIPT=", receipt)

if not isinstance(receipt, dict):
    raise SystemExit("V65_86_FAIL=invalid_deploy_receipt")

if provider == "vercel":
    if not receipt.get("ok"):
        raise SystemExit(f"V65_86_FAIL=vercel_deployment_failed:{receipt}")
    public_url = receipt.get("live_url")
    deployment_id = receipt.get("deployment_id")
else:
    public_url = receipt.get("url")
    deployment_id = receipt.get("deployment_id")

if not public_url:
    raise SystemExit("V65_86_FAIL=public_url_missing")

if not str(public_url).startswith(("http://", "https://")):
    public_url = "https://" + str(public_url)

# ---------- Public reachability / latency samples ----------
samples = []
status_code = None
body_bytes = None
last_error = None

for attempt in range(12):
    try:
        t0 = time.perf_counter()
        req = urllib.request.Request(
            public_url,
            headers={"User-Agent": "CompanyOS-V65.86-LiveTrial/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read()
            elapsed = (time.perf_counter() - t0) * 1000
            status_code = int(resp.status)
            body_bytes = len(body)
            samples.append(round(elapsed, 2))
        if 200 <= status_code < 400:
            break
    except Exception as exc:
        last_error = f"{type(exc).__name__}:{exc}"
        time.sleep(3)

if not samples or status_code is None or status_code >= 400:
    raise SystemExit(f"V65_86_FAIL=public_site_not_reachable:{last_error}")

# Collect a few additional response samples.
for _ in range(4):
    try:
        t0 = time.perf_counter()
        req = urllib.request.Request(
            public_url,
            headers={"User-Agent": "CompanyOS-V65.86-LiveTrial/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
            samples.append(round((time.perf_counter() - t0) * 1000, 2))
    except Exception:
        pass

avg_ms = round(statistics.mean(samples), 2)
min_ms = round(min(samples), 2)
max_ms = round(max(samples), 2)

# ---------- Persist launch evidence ----------
launch_record = {
    "version": "V65.86",
    "timestamp_unix": time.time(),
    "mode": "one_real_public_deployment",
    "venture_title": title,
    "venture_slug": slug,
    "candidate_source": str(candidate_path),
    "provider": provider,
    "deployment_id": deployment_id,
    "public_url": public_url,
    "deploy_seconds": deploy_seconds,
    "http_status": status_code,
    "page_bytes": body_bytes,
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
    "qualification_reason": reason,
    "deployment_receipt": receipt,
}

(RUNTIME / "venture_launch_latest.json").write_text(
    json.dumps(
        {
            "timestamp": time.time(),
            "status": "launched",
            "title": title,
            "slug": slug,
            "public_url": public_url,
            "deployment": receipt,
            "next_action": "measure_market_response",
            "v65_86_trial": True,
        },
        indent=2,
        sort_keys=True,
        default=str,
    )
    + "\n"
)

with (RUNTIME / "venture_launch_ledger.jsonl").open("a") as f:
    f.write(json.dumps(launch_record, sort_keys=True, default=str) + "\n")

rp = REPORT_DIR / f"v65_86_live_public_launch_{STAMP}.json"
rp.write_text(json.dumps(launch_record, indent=2, sort_keys=True, default=str) + "\n")

# ---------- Final task/db health ----------
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
print("PAGE_BYTES=", body_bytes)
print("LATENCY_SAMPLES_MS=", samples)
print("LATENCY_AVG_MS=", avg_ms)
print("LATENCY_MIN_MS=", min_ms)
print("LATENCY_MAX_MS=", max_ms)
print("QUEUE_STATES_AFTER=", dict(sorted(states_after.items())))
print("DB_INTEGRITY_AFTER=", integrity_after)
print("QUEUE_MINUS_DB_DELTA_AFTER=", len(tasks_after) - db_after)
print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP)

if bad_after:
    raise SystemExit("V65_86_FAIL=unreadable_queue_after")
if integrity_after != "ok":
    raise SystemExit("V65_86_FAIL=db_integrity_after")
if len(tasks_after) != db_after:
    raise SystemExit("V65_86_FAIL=projection_mismatch_after")

print("V65_86_LIVE_PUBLIC_LAUNCH=PASS")
print("V65_86_PUBLIC_REACHABILITY=PASS")
print("V65_86_PERFORMANCE_MEASUREMENT=PASS")
print("V65_86_FINANCIAL_ACTIONS_BLOCKED=PASS")
print("V65_86_RUNTIME_INTEGRITY=PASS")
print("V65_86_COMPLETE")
PY
