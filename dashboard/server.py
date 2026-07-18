#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from datetime import datetime
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MEMORY_DIR = ROOT_DIR / "ceo_memory"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

HOST = os.environ.get(
    "COMPANYOS_DASHBOARD_HOST",
    "127.0.0.1",
)

PORT = int(
    os.environ.get(
        "COMPANYOS_DASHBOARD_PORT",
        "8765",
    )
)

PORTFOLIO_FILE = MEMORY_DIR / "portfolio.json"
HEALTH_FILE = MEMORY_DIR / "company_health.json"
ROADMAP_FILE = MEMORY_DIR / "roadmap.json"
TARGETS_FILE = MEMORY_DIR / "growth_targets.json"
CAPITAL_FILE = MEMORY_DIR / "capital_allocations.json"
DECISIONS_FILE = MEMORY_DIR / "executive_decisions.json"
COMPANY_STATE_FILE = MEMORY_DIR / "company_state.json"
PROFIT_FILE = MEMORY_DIR / "profit_summary.json"
SALES_FILE = MEMORY_DIR / "sales_summary.json"
CUSTOMER_FILE = MEMORY_DIR / "customer_summary.json"
TASKS_FILE = MEMORY_DIR / "tasks.json"


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def safe_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [
            item
            for item in value
            if isinstance(item, dict)
        ]
    return []


def dashboard_data() -> dict[str, Any]:
    portfolio = load_json(PORTFOLIO_FILE, {})
    health = load_json(HEALTH_FILE, {})
    roadmap = load_json(ROADMAP_FILE, {})
    targets = load_json(TARGETS_FILE, {})
    capital = load_json(CAPITAL_FILE, {})
    decisions = safe_list(
        load_json(DECISIONS_FILE, [])
    )
    company = load_json(COMPANY_STATE_FILE, {})
    profit = load_json(PROFIT_FILE, {})
    sales = load_json(SALES_FILE, {})
    customers = load_json(CUSTOMER_FILE, {})
    tasks = safe_list(load_json(TASKS_FILE, []))

    ventures = safe_list(
        portfolio.get("ventures", [])
        if isinstance(portfolio, dict)
        else []
    )

    top_venture = ventures[0] if ventures else {}

    pending_decisions = [
        item
        for item in decisions
        if str(item.get("status", "")).lower()
        == "recommended"
    ]

    pending_tasks = sum(
        1
        for task in tasks
        if str(task.get("status", "")).lower()
        in {"pending", "queued", "waiting"}
    )

    completed_tasks = sum(
        1
        for task in tasks
        if str(task.get("status", "")).lower()
        in {"completed", "done", "success", "successful"}
    )

    failed_tasks = sum(
        1
        for task in tasks
        if str(task.get("status", "")).lower()
        in {"failed", "error", "rejected"}
    )

    return {
        "success": True,
        "updated_at": datetime.now().isoformat(),
        "company_name": (
            company.get("company_name")
            if isinstance(company, dict)
            else "NexusAI Solutions"
        ) or "NexusAI Solutions",
        "company_health": (
            health.get("health")
            if isinstance(health, dict)
            else "unknown"
        ) or "unknown",
        "average_venture_score": float(
            health.get("average_venture_score", 0)
            if isinstance(health, dict)
            else 0
        ),
        "total_ventures": int(
            portfolio.get("total_ventures", 0)
            if isinstance(portfolio, dict)
            else 0
        ),
        "active_ventures": int(
            portfolio.get("active_ventures", 0)
            if isinstance(portfolio, dict)
            else 0
        ),
        "total_products": int(
            portfolio.get("total_products", 0)
            if isinstance(portfolio, dict)
            else 0
        ),
        "total_customers": int(
            portfolio.get("total_customers", 0)
            if isinstance(portfolio, dict)
            else 0
        ),
        "total_revenue_usd": float(
            portfolio.get("total_revenue_usd", 0)
            if isinstance(portfolio, dict)
            else 0
        ),
        "total_expenses_usd": float(
            portfolio.get("total_expenses_usd", 0)
            if isinstance(portfolio, dict)
            else 0
        ),
        "total_profit_usd": float(
            portfolio.get("total_profit_usd", 0)
            if isinstance(portfolio, dict)
            else 0
        ),
        "cash_balance_usd": float(
            profit.get("cash_balance_usd", 0)
            if isinstance(profit, dict)
            else 0
        ),
        "orders": int(
            sales.get("total_orders", 0)
            if isinstance(sales, dict)
            else 0
        ),
        "conversion_rate_percent": float(
            sales.get("conversion_rate_percent", 0)
            if isinstance(sales, dict)
            else 0
        ),
        "customer_lifetime_value_usd": float(
            customers.get("customer_lifetime_value_usd", 0)
            if isinstance(customers, dict)
            else 0
        ),
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "pending_decisions": len(pending_decisions),
        "top_venture": top_venture,
        "roadmap": (
            roadmap.get("priorities", [])
            if isinstance(roadmap, dict)
            else []
        ),
        "growth_targets": targets,
        "capital_plan": capital,
        "decisions": pending_decisions[-20:],
    }


def run_portfolio_review() -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "companyos" / "portfolioctl"),
            "review",
        ],
        cwd=str(ROOT_DIR),
        text=True,
        capture_output=True,
        timeout=120,
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": (
                result.stderr.strip()
                or result.stdout.strip()
                or "Portfolio review failed"
            ),
        }

    return {
        "success": True,
        "status": "portfolio_review_complete",
        "output": result.stdout[-5000:],
    }


def approve_decision(
    decision_id: str,
) -> dict[str, Any]:
    if not decision_id:
        return {
            "success": False,
            "error": "decision_id is required",
        }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "companyos" / "portfolioctl"),
            "approve",
            decision_id,
        ],
        cwd=str(ROOT_DIR),
        text=True,
        capture_output=True,
        timeout=60,
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": (
                result.stderr.strip()
                or result.stdout.strip()
                or "Approval failed"
            ),
        }

    return {
        "success": True,
        "status": "decision_approved",
        "output": result.stdout[-3000:],
    }


def page_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1">
<title>CompanyOS Executive Dashboard</title>
<style>
:root {
  color-scheme: dark;
  font-family: system-ui, sans-serif;
  background: #090b0f;
  color: #f5f7fa;
}
* { box-sizing: border-box; }
body {
  margin: 0 auto;
  padding: 22px;
  max-width: 1000px;
}
h1, h2, h3 { margin-top: 0; }
.header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 18px;
  margin-bottom: 22px;
}
.card {
  background: #15191f;
  border: 1px solid #2a3039;
  border-radius: 18px;
  padding: 20px;
  margin-bottom: 18px;
  overflow: hidden;
}
.grid {
  display: grid;
  grid-template-columns:
    repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.metric {
  font-size: 2rem;
  font-weight: 800;
  margin-top: 8px;
}
.muted { color: #a7afb9; }
.good { color: #70df9b; }
.warn { color: #ffd166; }
.bad { color: #ff7b86; }
button {
  border: 0;
  border-radius: 12px;
  padding: 13px 17px;
  font-size: 1rem;
  font-weight: 800;
  cursor: pointer;
}
table {
  width: 100%;
  border-collapse: collapse;
}
td, th {
  text-align: left;
  padding: 12px 8px;
  border-bottom: 1px solid #2a3039;
  vertical-align: top;
}
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
@media (max-width: 600px) {
  .header { display: block; }
  .header button { margin-top: 14px; width: 100%; }
}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1 id="companyName">CompanyOS</h1>
    <div class="muted" id="updatedAt">Loading...</div>
  </div>
  <button onclick="refreshPortfolio()">
    Refresh portfolio
  </button>
</div>

<div class="grid" id="metrics"></div>

<div class="card">
  <h2>Top venture</h2>
  <div id="topVenture">Loading...</div>
</div>

<div class="card">
  <h2>Capital plan</h2>
  <div id="capitalPlan">Loading...</div>
</div>

<div class="card">
  <h2>Growth targets</h2>
  <div id="growthTargets">Loading...</div>
</div>

<div class="card">
  <h2>Executive roadmap</h2>
  <div id="roadmap">Loading...</div>
</div>

<div class="card">
  <h2>Decisions awaiting approval</h2>
  <div id="decisions">Loading...</div>
</div>

<script>
function money(value) {
  return "$" + Number(value || 0).toFixed(2);
}

function scoreClass(value) {
  value = Number(value || 0);
  if (value >= 7) return "good";
  if (value >= 4) return "warn";
  return "bad";
}

async function loadDashboard() {
  const response = await fetch("/api/dashboard");
  const data = await response.json();

  document.getElementById("companyName").textContent =
    data.company_name + " Executive Dashboard";

  document.getElementById("updatedAt").textContent =
    "Updated " + new Date(data.updated_at).toLocaleString();

  const metrics = [
    ["Company health", data.company_health],
    ["Venture score", Number(data.average_venture_score).toFixed(2)],
    ["Active ventures", data.active_ventures],
    ["Products", data.total_products],
    ["Customers", data.total_customers],
    ["Orders", data.orders],
    ["Revenue", money(data.total_revenue_usd)],
    ["Expenses", money(data.total_expenses_usd)],
    ["Profit", money(data.total_profit_usd)],
    ["Cash balance", money(data.cash_balance_usd)],
    ["Conversion rate", Number(data.conversion_rate_percent).toFixed(2) + "%"],
    ["Pending decisions", data.pending_decisions]
  ];

  document.getElementById("metrics").innerHTML =
    metrics.map(item => `
      <div class="card">
        <div class="muted">${item[0]}</div>
        <div class="metric">${item[1]}</div>
      </div>
    `).join("");

  const venture = data.top_venture || {};
  const score = venture.scores?.final_score || 0;

  document.getElementById("topVenture").innerHTML = `
    <h3>${venture.name || "No venture"}</h3>
    <p>
      Score:
      <strong class="${scoreClass(score)}">
        ${Number(score).toFixed(2)} / 10
      </strong>
    </p>
    <p>Recommendation:
      <strong>${venture.recommended_action || "none"}</strong>
    </p>
    <p>${venture.recommendation_reason || ""}</p>
    <div class="grid">
      <div>Products: <strong>${venture.products || 0}</strong></div>
      <div>Customers: <strong>${venture.customers || 0}</strong></div>
      <div>Orders: <strong>${venture.orders || 0}</strong></div>
      <div>Profit: <strong>${money(venture.profit_usd)}</strong></div>
    </div>
  `;

  const allocation =
    data.capital_plan?.allocation || {};

  document.getElementById("capitalPlan").innerHTML = `
    <p>
      Source profit:
      <strong>${money(data.capital_plan?.source_profit_usd)}</strong>
    </p>
    <div class="grid">
      <div>Retained cash:
        <strong>${money(allocation.retained_cash_usd)}</strong>
      </div>
      <div>Marketing:
        <strong>${money(allocation.marketing_usd)}</strong>
      </div>
      <div>Product development:
        <strong>${money(allocation.product_development_usd)}</strong>
      </div>
      <div>Research:
        <strong>${money(allocation.research_usd)}</strong>
      </div>
      <div>New venture reserve:
        <strong>${money(allocation.new_venture_reserve_usd)}</strong>
      </div>
    </div>
    <p class="muted">
      Recommendations only. Automatic spending is disabled.
    </p>
  `;

  const targets = data.growth_targets || {};

  document.getElementById("growthTargets").innerHTML = `
    <div class="grid">
      <div>Revenue target:
        <strong>${money(targets.next_revenue_target_usd)}</strong>
      </div>
      <div>Customer target:
        <strong>${targets.next_customer_target || 0}</strong>
      </div>
      <div>Minimum validation score:
        <strong>${targets.minimum_validation_score || 0}</strong>
      </div>
      <div>Maximum failed tasks:
        <strong>${targets.maximum_failed_tasks_per_cycle || 0}</strong>
      </div>
    </div>
  `;

  const roadmap = data.roadmap || [];

  document.getElementById("roadmap").innerHTML =
    roadmap.length
      ? `<table>
          <thead>
            <tr>
              <th>Priority</th>
              <th>Venture</th>
              <th>Action</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
          ${roadmap.map(item => `
            <tr>
              <td>${item.priority}</td>
              <td>${item.venture_name || item.venture_id}</td>
              <td>${item.action}</td>
              <td>${item.reason}</td>
            </tr>
          `).join("")}
          </tbody>
        </table>`
      : "<p>No roadmap priorities yet.</p>";

  const decisions = data.decisions || [];

  document.getElementById("decisions").innerHTML =
    decisions.length
      ? decisions.map(item => `
          <div class="card">
            <strong>${item.action}</strong>
            <p>${item.reason}</p>
            <p class="muted">${item.id}</p>
            <button onclick="approveDecision('${item.id}')">
              Approve recommendation
            </button>
          </div>
        `).join("")
      : "<p>No decisions awaiting approval.</p>";
}

async function refreshPortfolio() {
  const response = await fetch(
    "/api/portfolio/review",
    { method: "POST" }
  );

  const result = await response.json();

  if (!result.success) {
    alert(result.error || "Portfolio review failed");
    return;
  }

  await loadDashboard();
}

async function approveDecision(decisionId) {
  const response = await fetch(
    "/api/decision/approve",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        decision_id: decisionId
      })
    }
  );

  const result = await response.json();

  if (!result.success) {
    alert(result.error || "Approval failed");
    return;
  }

  await loadDashboard();
}

loadDashboard();
setInterval(loadDashboard, 30000);
</script>

</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def send_json(
        self,
        data: Any,
        status: int = 200,
    ) -> None:
        payload = json.dumps(
            data,
            indent=2,
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(payload)),
        )
        self.end_headers()
        self.wfile.write(payload)

    def send_html(
        self,
        value: str,
    ) -> None:
        payload = value.encode("utf-8")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(payload)),
        )
        self.end_headers()
        self.wfile.write(payload)

    def read_json(self) -> dict[str, Any]:
        length = int(
            self.headers.get(
                "Content-Length",
                "0",
            )
        )

        if length > 10000:
            raise ValueError(
                "Request body is too large"
            )

        raw = self.rfile.read(length)

        if not raw:
            return {}

        value = json.loads(
            raw.decode("utf-8")
        )

        if not isinstance(value, dict):
            raise ValueError(
                "Request body must be an object"
            )

        return value

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/dashboard":
            self.send_json(
                dashboard_data()
            )
            return

        if path in {"/", "/index.html"}:
            self.send_html(
                page_html()
            )
            return

        self.send_json(
            {
                "success": False,
                "error": "Not found",
            },
            status=404,
        )

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        try:
            if path == "/api/portfolio/review":
                result = run_portfolio_review()

            elif path == "/api/decision/approve":
                body = self.read_json()

                result = approve_decision(
                    str(
                        body.get(
                            "decision_id",
                            "",
                        )
                    )
                )

            else:
                self.send_json(
                    {
                        "success": False,
                        "error": "Not found",
                    },
                    status=404,
                )
                return

            self.send_json(
                result,
                status=(
                    200
                    if result.get("success")
                    else 400
                ),
            )

        except Exception as error:
            self.send_json(
                {
                    "success": False,
                    "error": str(error),
                },
                status=400,
            )


def main() -> None:
    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler,
    )

    print("=" * 60)
    print("CompanyOS Executive Dashboard")
    print(f"Address: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
