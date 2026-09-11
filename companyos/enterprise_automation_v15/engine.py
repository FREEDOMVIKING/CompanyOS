import json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def append_jsonl(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

class EnterpriseAutomationV15:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/enterprise_automation_v15_450001_500000"
        self.storefront = self.home / "companyos_runtime/storefront_sales_v8_190001_220000"
        self.revenue = self.home / "companyos_runtime/autonomous_revenue_v11_280001_320000"
        self.crm = self.home / "companyos_runtime/customer_growth_crm_v13_360001_400000"
        self.commercial = self.home / "companyos_runtime/commercial_operations_v14_400001_450000"
        self.generated = self.home / "generated_ventures"
        self.records = self.home / "enterprise_records_v15"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def catalog(self):
        return read_json(self.storefront / "catalog.json", {"products": []}).get("products", [])

    def orders(self):
        return read_json(self.storefront / "orders.json", {"orders": []}).get("orders", [])

    def revenue_state(self):
        return read_json(self.live / "autonomous_revenue_v11_live.json", {})

    def crm_state(self):
        return read_json(self.live / "customer_growth_crm_v13_live.json", {})

    def commercial_state(self):
        return read_json(self.live / "commercial_operations_v14_live.json", {})

    def ventures(self):
        ventures = []
        if self.generated.exists():
            for p in sorted(self.generated.iterdir()):
                if not p.is_dir():
                    continue
                manifest = read_json(p / "venture.json", {})
                if not manifest:
                    manifest = read_json(p / "manifest.json", {})
                ventures.append({
                    "venture_id": manifest.get("venture_id", p.name),
                    "name": manifest.get("name", p.name.replace("-", " ").title()),
                    "status": manifest.get("status", "DISCOVERED"),
                    "workspace": str(p),
                    "priority": float(manifest.get("priority", 50) or 50),
                })
        if not ventures:
            ventures.append({
                "venture_id": "digital-products",
                "name": "Digital Products Portfolio",
                "status": "ACTIVE",
                "workspace": str(self.home / "generated_products_v7"),
                "priority": 80.0,
            })
        return ventures

    def portfolio_kpis(self):
        products = self.catalog()
        orders = self.orders()
        paid = [o for o in orders if o.get("status") in ("PAID", "FULFILLMENT_READY", "DELIVERED")]
        revenue = round(sum(float(o.get("amount_usd", 0) or 0) for o in paid), 2)
        crm = self.crm_state()
        return {
            "ventures": len(self.ventures()),
            "products": len(products),
            "orders_total": len(orders),
            "paid_orders": len(paid),
            "revenue_usd": revenue,
            "customers": int(crm.get("customers_total", 0) or 0),
            "open_support_tickets": int(crm.get("open_support_tickets", 0) or 0),
        }

    def cashflow_forecast(self, kpis):
        base = float(kpis.get("revenue_usd", 0) or 0)
        paying = int(kpis.get("paid_orders", 0) or 0)
        products = int(kpis.get("products", 0) or 0)
        return {
            "next_30_days": {
                "conservative": round(base + paying * 15 + products * 3, 2),
                "base": round(base + paying * 30 + products * 8, 2),
                "upside": round(base + paying * 60 + products * 18, 2),
            },
            "method": "bounded scenario model; not a guarantee",
        }

    def hiring_plan(self, kpis):
        roles = []
        if kpis["open_support_tickets"] >= 10:
            roles.append({"role": "Customer Support Specialist", "reason": "Support backlog threshold reached"})
        if kpis["products"] >= 10 and kpis["paid_orders"] >= 5:
            roles.append({"role": "Growth Operations Specialist", "reason": "Portfolio scale and sales volume justify support"})
        if kpis["ventures"] >= 3:
            roles.append({"role": "Portfolio Operations Manager", "reason": "Multi-venture coordination load"})
        if not roles:
            roles.append({"role": "No hire recommended", "reason": "Current activity does not justify added staffing"})
        return {
            "status": "DRAFT_REVIEW_REQUIRED",
            "roles": roles,
            "auto_hire": False,
        }

    def vendor_queue(self):
        return {
            "status": "REVIEW_REQUIRED",
            "vendors": [],
            "negotiation_auto_send": False,
            "note": "No vendor commitments will be created automatically.",
        }

    def procurement_recommendations(self, kpis):
        recs = []
        if kpis["products"] >= 5:
            recs.append({
                "item": "Storage and backup capacity review",
                "reason": "Growing product catalog",
                "action": "REVIEW",
            })
        if kpis["orders_total"] >= 20:
            recs.append({
                "item": "Email delivery capacity review",
                "reason": "Order volume threshold",
                "action": "REVIEW",
            })
        if not recs:
            recs.append({
                "item": "No procurement action",
                "reason": "Current usage remains below threshold",
                "action": "HOLD",
            })
        return recs

    def prioritize(self):
        ranked = []
        for v in self.ventures():
            score = float(v.get("priority", 0) or 0)
            if v.get("status") == "ACTIVE":
                score += 10
            ranked.append({**v, "priority_score": round(score, 2)})
        ranked.sort(key=lambda x: x["priority_score"], reverse=True)
        return ranked

    def intelligence_report(self, state):
        report = {
            "generated_at": now(),
            "headline": "CompanyOS Enterprise Daily Intelligence",
            "summary": {
                "portfolio_status": state["status"],
                "top_priority_venture": state["top_priority_venture"],
                "revenue_usd": state["kpis"]["revenue_usd"],
                "paid_orders": state["kpis"]["paid_orders"],
                "customers": state["kpis"]["customers"],
            },
            "risks": [
                "No verified customer demand yet" if state["kpis"]["paid_orders"] == 0 else "No critical sales risk detected",
                "Consequential actions remain review-gated",
            ],
            "recommended_next_action": (
                "Drive first verified customer purchase"
                if state["kpis"]["paid_orders"] == 0
                else "Scale the highest-converting product"
            ),
        }
        write_json(self.records / "daily_intelligence_latest.json", report)
        return report

    def run_cycle(self):
        kpis = self.portfolio_kpis()
        ranked = self.prioritize()
        state = {
            "status": "enterprise_automation_ready",
            "kpis": kpis,
            "cashflow_forecast": self.cashflow_forecast(kpis),
            "hiring_plan": self.hiring_plan(kpis),
            "vendor_queue": self.vendor_queue(),
            "procurement_recommendations": self.procurement_recommendations(kpis),
            "venture_priorities": ranked,
            "top_priority_venture": ranked[0]["name"] if ranked else None,
            "external_commitments_enabled": False,
            "dashboard_url": "http://127.0.0.1:8777",
            "updated_at": now(),
        }
        state["daily_intelligence"] = self.intelligence_report(state)
        write_json(self.live / "enterprise_automation_v15_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "enterprise_automation_v15_cycle",
            "event_type": "enterprise_automation_v15_cycle",
            "state": state,
        })
        return state
