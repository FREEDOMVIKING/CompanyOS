#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
DASHBOARD="$ROOT/dashboard"
BACKUP="$ROOT/backups/phase16_step7_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$DASHBOARD" "$BACKUP"

echo "============================================================"
echo " Phase 16 Step 7 - Business Intelligence Dashboard"
echo "============================================================"

for file in \
  "$AGENTS/business_intelligence.py" \
  "$CTL/bictl" \
  "$MEMORY/business_intelligence_config.json" \
  "$MEMORY/business_intelligence_snapshot.json" \
  "$MEMORY/business_intelligence_health.json" \
  "$DASHBOARD/bi_server.py" \
  "$DASHBOARD/index.html" \
  "$DASHBOARD/app.js" \
  "$DASHBOARD/styles.css"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/business_intelligence_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_snapshot_generation": true,
  "automatic_internal_recommendations": true,
  "automatic_external_execution": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "owner_approval_required_for_external_actions": true,
  "dashboard_host": "127.0.0.1",
  "dashboard_port": 8781
}
JSON

cat > "$AGENTS/business_intelligence.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "business_intelligence_config.json"
SNAPSHOT = MEMORY / "business_intelligence_snapshot.json"
HEALTH = MEMORY / "business_intelligence_health.json"
AUDIT = MEMORY / "business_intelligence_audit.json"

LEADS = MEMORY / "crm_leads.json"
QUOTES = MEMORY / "quote_registry.json"
PROJECTS = MEMORY / "project_registry.json"
MILESTONES = MEMORY / "project_milestones.json"
FOLLOWUPS = MEMORY / "sales_followups.json"
INVOICES = MEMORY / "invoice_registry.json"
PAYMENTS = MEMORY / "payment_registry.json"
EXPENSES = MEMORY / "expense_registry.json"
FINANCIAL_KPIS = MEMORY / "financial_kpis.json"
EXECUTIVE_SUMMARY = MEMORY / "daily_executive_summary.json"
ACTIVITY_FEED = MEMORY / "business_activity_feed.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []
    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })
    save_json(AUDIT, records[-1000:])


def money(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except Exception:
        return 0.0


def build_recommendations(
    leads: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    followups: list[dict[str, Any]],
    invoices: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    recommendations = []

    pending_followups = [
        item for item in followups
        if item.get("status") == "pending"
    ]
    overdue_invoices = [
        item for item in invoices
        if item.get("status") in {"issued", "partially_paid"}
        and money(item.get("balance_due")) > 0
    ]
    stalled_projects = [
        item for item in projects
        if item.get("status") in {"planning", "waiting"}
        and int(item.get("progress_percent") or 0) < 25
    ]
    new_leads = [
        item for item in leads
        if item.get("status") == "new"
    ]

    if pending_followups:
        recommendations.append({
            "priority": "high",
            "type": "sales",
            "title": "Review pending follow-ups",
            "detail": f"{len(pending_followups)} follow-up(s) are waiting for owner review.",
            "external_action_required": False,
        })

    if overdue_invoices:
        recommendations.append({
            "priority": "high",
            "type": "finance",
            "title": "Review outstanding invoices",
            "detail": f"{len(overdue_invoices)} invoice(s) still have balances due.",
            "external_action_required": False,
        })

    if stalled_projects:
        recommendations.append({
            "priority": "medium",
            "type": "operations",
            "title": "Review stalled projects",
            "detail": f"{len(stalled_projects)} project(s) have low progress.",
            "external_action_required": False,
        })

    if new_leads:
        recommendations.append({
            "priority": "medium",
            "type": "crm",
            "title": "Qualify new leads",
            "detail": f"{len(new_leads)} new lead(s) need internal review.",
            "external_action_required": False,
        })

    if money(metrics.get("net_cash_position")) < 0:
        recommendations.append({
            "priority": "high",
            "type": "finance",
            "title": "Protect cash flow",
            "detail": "Recorded expenses currently exceed recorded payments.",
            "external_action_required": False,
        })

    if not recommendations:
        recommendations.append({
            "priority": "low",
            "type": "general",
            "title": "Company systems stable",
            "detail": "No major internal warnings detected.",
            "external_action_required": False,
        })

    return recommendations


def calculate_health(
    pending_followups: int,
    overdue_invoices: int,
    stalled_projects: int,
    net_cash: float,
) -> tuple[str, int]:
    score = 100
    score -= min(pending_followups * 5, 20)
    score -= min(overdue_invoices * 10, 30)
    score -= min(stalled_projects * 8, 24)

    if net_cash < 0:
        score -= 20

    score = max(0, min(100, score))

    if score >= 85:
        return "healthy", score
    if score >= 65:
        return "stable", score
    return "needs_review", score


def generate_snapshot() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "business_intelligence_disabled",
        }
        audit("generate", result)
        return result

    leads = load_json(LEADS, {}).get("leads", [])
    quotes = load_json(QUOTES, {}).get("quotes", [])
    projects = load_json(PROJECTS, {}).get("projects", [])
    milestones = load_json(MILESTONES, {}).get("milestones", [])
    followups = load_json(FOLLOWUPS, {}).get("followups", [])
    invoices = load_json(INVOICES, {}).get("invoices", [])
    payments = load_json(PAYMENTS, {}).get("payments", [])
    expenses = load_json(EXPENSES, {}).get("expenses", [])
    financial_metrics = load_json(
        FINANCIAL_KPIS,
        {},
    ).get("metrics", {})
    executive_summary = load_json(
        EXECUTIVE_SUMMARY,
        {},
    ).get("summary", {})
    activity = load_json(
        ACTIVITY_FEED,
        {},
    ).get("activities", [])

    pipeline_value = sum(
        money(item.get("estimate_amount"))
        for item in leads
        if item.get("status") not in {"won", "lost"}
    )
    won_value = sum(
        money(item.get("estimate_amount"))
        for item in leads
        if item.get("status") == "won"
    )
    receivables = sum(
        money(item.get("balance_due"))
        for item in invoices
    )
    cash_received = sum(
        money(item.get("amount"))
        for item in payments
    )
    expense_total = sum(
        money(item.get("amount"))
        for item in expenses
    )
    net_cash = round(cash_received - expense_total, 2)

    pending_followups = sum(
        1 for item in followups
        if item.get("status") == "pending"
    )
    overdue_invoices = sum(
        1 for item in invoices
        if item.get("status") in {"issued", "partially_paid"}
        and money(item.get("balance_due")) > 0
    )
    stalled_projects = sum(
        1 for item in projects
        if item.get("status") in {"planning", "waiting"}
        and int(item.get("progress_percent") or 0) < 25
    )
    completed_milestones = sum(
        1 for item in milestones
        if item.get("status") == "completed"
    )

    company_health, company_score = calculate_health(
        pending_followups,
        overdue_invoices,
        stalled_projects,
        net_cash,
    )

    recommendations = build_recommendations(
        leads,
        projects,
        followups,
        invoices,
        financial_metrics,
    )

    snapshot = {
        "generated_at": now(),
        "company_health": company_health,
        "company_score": company_score,
        "crm": {
            "total_leads": len(leads),
            "new_leads": sum(
                1 for item in leads
                if item.get("status") == "new"
            ),
            "won_leads": sum(
                1 for item in leads
                if item.get("status") == "won"
            ),
            "lost_leads": sum(
                1 for item in leads
                if item.get("status") == "lost"
            ),
            "pipeline_value": round(pipeline_value, 2),
            "won_value": round(won_value, 2),
        },
        "sales": {
            "quote_count": len(quotes),
            "pending_followups": pending_followups,
            "conversion_rate_percent": (
                round(
                    (
                        sum(
                            1 for item in leads
                            if item.get("status") == "won"
                        )
                        / len(leads)
                    ) * 100,
                    2,
                )
                if leads
                else 0.0
            ),
        },
        "projects": {
            "total_projects": len(projects),
            "active_projects": sum(
                1 for item in projects
                if item.get("status") not in {"completed", "cancelled"}
            ),
            "stalled_projects": stalled_projects,
            "total_milestones": len(milestones),
            "completed_milestones": completed_milestones,
            "average_completion_percent": (
                round(
                    sum(
                        int(item.get("progress_percent") or 0)
                        for item in projects
                    ) / len(projects),
                    2,
                )
                if projects
                else 0.0
            ),
        },
        "finance": {
            "total_invoiced": round(
                sum(money(item.get("total")) for item in invoices),
                2,
            ),
            "cash_received": round(cash_received, 2),
            "accounts_receivable": round(receivables, 2),
            "recorded_expenses": round(expense_total, 2),
            "net_cash_position": net_cash,
            "overdue_invoice_count": overdue_invoices,
        },
        "warnings": {
            "pending_followups": pending_followups,
            "overdue_invoices": overdue_invoices,
            "stalled_projects": stalled_projects,
        },
        "recommendations": recommendations,
        "executive_summary": executive_summary,
        "recent_activity": activity[-10:],
        "automatic_external_execution": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    save_json(
        SNAPSHOT,
        {
            "schema_version": 1,
            "snapshot": snapshot,
            "last_updated_at": now(),
        },
    )

    save_json(
        HEALTH,
        {
            "healthy": True,
            "company_health": company_health,
            "company_score": company_score,
            "last_generated_at": now(),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "business_intelligence_snapshot_generated",
        "snapshot": snapshot,
    }

    audit("generate", result)
    return result


def show_snapshot() -> dict[str, Any]:
    store = load_json(SNAPSHOT, {})
    snapshot = store.get("snapshot")

    result = {
        "success": bool(snapshot),
        "status": "business_intelligence_snapshot",
        "snapshot": snapshot,
    }

    audit("show", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "business_intelligence_status",
        "enabled": config.get("enabled", False),
        "automatic_snapshot_generation": config.get(
            "automatic_snapshot_generation", False
        ),
        "automatic_internal_recommendations": config.get(
            "automatic_internal_recommendations", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "dashboard_host": config.get("dashboard_host"),
        "dashboard_port": config.get("dashboard_port"),
        "health": health,
    }

    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "generate":
            return print_result(generate_snapshot())

        if action == "show":
            return print_result(show_snapshot())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_bi_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "business_intelligence_error",
            "error": str(exc),
        }

        save_json(
            HEALTH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )

        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/business_intelligence.py"

cat > "$CTL/bictl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "business_intelligence.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/bictl"

cat > "$DASHBOARD/index.html" <<'HTML'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Business Intelligence</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<header>
  <h1>CompanyOS Business Intelligence</h1>
  <p id="updated">Loading snapshot...</p>
  <button id="refresh">Refresh dashboard</button>
</header>

<main>
  <section class="grid">
    <article>
      <span>Company health</span>
      <strong id="health">—</strong>
    </article>
    <article>
      <span>Company score</span>
      <strong id="score">—</strong>
    </article>
    <article>
      <span>Pipeline value</span>
      <strong id="pipeline">—</strong>
    </article>
    <article>
      <span>Cash position</span>
      <strong id="cash">—</strong>
    </article>
    <article>
      <span>Active projects</span>
      <strong id="projects">—</strong>
    </article>
    <article>
      <span>Pending follow-ups</span>
      <strong id="followups">—</strong>
    </article>
  </section>

  <section class="panel">
    <h2>Financial overview</h2>
    <div id="finance"></div>
  </section>

  <section class="panel">
    <h2>Strategic recommendations</h2>
    <div id="recommendations"></div>
  </section>

  <section class="panel">
    <h2>Recent activity</h2>
    <div id="activity"></div>
  </section>
</main>

<script src="app.js"></script>
</body>
</html>
HTML

cat > "$DASHBOARD/styles.css" <<'CSS'
*{box-sizing:border-box}
body{
  margin:0;
  font-family:system-ui,sans-serif;
  background:#090b10;
  color:#f5f7fa;
}
header{
  padding:24px;
  border-bottom:1px solid #252a34;
  background:#0d1016;
}
h1{margin:0 0 8px}
header p{color:#aeb6c3}
button{
  width:100%;
  padding:14px;
  border:0;
  border-radius:10px;
  font-weight:700;
}
main{
  width:min(1000px,calc(100% - 28px));
  margin:20px auto 40px;
}
.grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:14px;
}
article,.panel{
  background:#141820;
  border:1px solid #2a303b;
  border-radius:14px;
  padding:18px;
}
article span{
  display:block;
  color:#aeb6c3;
  margin-bottom:10px;
}
article strong{
  font-size:2rem;
}
.panel{
  margin-top:16px;
}
.item{
  padding:12px 0;
  border-bottom:1px solid #2a303b;
}
.item:last-child{border-bottom:0}
.priority-high{font-weight:800}
small{color:#aeb6c3}
CSS

cat > "$DASHBOARD/app.js" <<'JS'
function money(value){
  return new Intl.NumberFormat(
    "en-US",
    {style:"currency",currency:"USD"}
  ).format(Number(value||0));
}

function item(title,detail,extra=""){
  return `<div class="item"><strong>${title}</strong><br>`+
         `<small>${detail}</small>${extra}</div>`;
}

async function load(){
  const response=await fetch("/api/snapshot",{cache:"no-store"});
  const payload=await response.json();
  const s=payload.snapshot||{};

  document.getElementById("updated").textContent=
    `Updated ${s.generated_at||"unknown"}`;
  document.getElementById("health").textContent=
    s.company_health||"unknown";
  document.getElementById("score").textContent=
    s.company_score??0;
  document.getElementById("pipeline").textContent=
    money(s.crm?.pipeline_value);
  document.getElementById("cash").textContent=
    money(s.finance?.net_cash_position);
  document.getElementById("projects").textContent=
    s.projects?.active_projects??0;
  document.getElementById("followups").textContent=
    s.sales?.pending_followups??0;

  const f=s.finance||{};
  document.getElementById("finance").innerHTML=
    item("Total invoiced",money(f.total_invoiced))+
    item("Cash received",money(f.cash_received))+
    item("Accounts receivable",money(f.accounts_receivable))+
    item("Recorded expenses",money(f.recorded_expenses));

  document.getElementById("recommendations").innerHTML=
    (s.recommendations||[]).map(r=>
      item(
        r.title,
        r.detail,
        `<br><small class="priority-${r.priority}">Priority: ${r.priority}</small>`
      )
    ).join("")||item("No recommendations","No data available.");

  document.getElementById("activity").innerHTML=
    (s.recent_activity||[]).slice().reverse().map(a=>
      item(a.title||a.activity_type, a.created_at||"")
    ).join("")||item("No activity","No activity recorded yet.");
}

document.getElementById("refresh").addEventListener("click",async()=>{
  await fetch("/api/refresh",{method:"POST"});
  await load();
});

load().catch(error=>{
  document.getElementById("updated").textContent=`Error: ${error}`;
});
JS

cat > "$DASHBOARD/bi_server.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path.home() / "companyos"
DASHBOARD = ROOT / "dashboard"
SNAPSHOT = ROOT / "ceo_memory" / "business_intelligence_snapshot.json"
BICTL = ROOT / "companyos" / "bictl"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        relative = urlparse(path).path.lstrip("/") or "index.html"
        return str(DASHBOARD / relative)

    def send_json(self, value: object, status: int = 200) -> None:
        body = json.dumps(value, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/snapshot":
            try:
                data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
                self.send_json(data)
            except Exception as exc:
                self.send_json(
                    {"success": False, "error": str(exc)},
                    500,
                )
            return

        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path == "/api/refresh":
            result = subprocess.run(
                [sys.executable, str(BICTL), "generate"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            try:
                payload = json.loads(result.stdout)
            except Exception:
                payload = {
                    "success": False,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

            self.send_json(
                payload,
                200 if result.returncode == 0 else 500,
            )
            return

        self.send_json({"success": False, "error": "not_found"}, 404)


def main() -> None:
    host = "127.0.0.1"
    port = 8781
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Open http://{host}:{port}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
PY

chmod +x "$DASHBOARD/bi_server.py"

echo "[1/6] Compiling..."
python -m py_compile \
  "$AGENTS/business_intelligence.py" \
  "$CTL/bictl" \
  "$DASHBOARD/bi_server.py"

echo "[2/6] Generating business intelligence snapshot..."
python "$CTL/bictl" generate

echo "[3/6] Checking snapshot..."
python "$CTL/bictl" show
python "$CTL/bictl" status

echo "[4/6] Checking dashboard files..."
test -s "$DASHBOARD/index.html"
test -s "$DASHBOARD/styles.css"
test -s "$DASHBOARD/app.js"
test -s "$DASHBOARD/bi_server.py"

echo "[5/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "business_intelligence.py",
    root / "companyos" / "bictl",
    root / "dashboard" / "bi_server.py",
    root / "dashboard" / "index.html",
    root / "dashboard" / "styles.css",
    root / "dashboard" / "app.js",
    root / "ceo_memory" / "business_intelligence_config.json",
    root / "ceo_memory" / "business_intelligence_snapshot.json",
]

for path in required:
    if not path.exists():
        errors.append(f"Missing: {path}")
    elif path.stat().st_size <= 0:
        errors.append(f"Empty: {path}")

for path in required[:3]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile error: {exc}")

try:
    config = json.loads(required[6].read_text(encoding="utf-8"))

    for field in [
        "automatic_external_execution",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    snapshot = json.loads(
        required[7].read_text(encoding="utf-8")
    ).get("snapshot", {})

    for field in [
        "company_health",
        "company_score",
        "crm",
        "sales",
        "projects",
        "finance",
        "recommendations",
    ]:
        if field not in snapshot:
            errors.append(f"Snapshot missing field: {field}")

except Exception as exc:
    errors.append(f"Snapshot error: {exc}")

print("--------------------------------------------")
print("Phase 16 Step 7 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo "[6/6] Complete."

echo
echo "============================================================"
echo " PHASE 16 STEP 7 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/bictl generate"
echo "  python companyos/bictl show"
echo "  python companyos/bictl status"
echo "  python dashboard/bi_server.py"
echo
echo "Dashboard:"
echo "  http://127.0.0.1:8781"
