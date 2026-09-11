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

class ExecutiveIntelligenceV16:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/executive_intelligence_v16_500001_550000"
        self.records = self.home / "executive_intelligence_records_v16"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

        self.modules = {
            "revenue": self.live / "autonomous_revenue_v11_live.json",
            "marketing": self.live / "autonomous_sales_marketing_v12_live.json",
            "crm": self.live / "customer_growth_crm_v13_live.json",
            "commercial": self.live / "commercial_operations_v14_live.json",
            "enterprise": self.live / "enterprise_automation_v15_live.json",
        }

    def module_states(self):
        result = {}
        for name, path in self.modules.items():
            data = read_json(path, {})
            result[name] = {
                "available": bool(data),
                "status": data.get("status"),
                "updated_at": data.get("updated_at"),
                "data": data,
            }
        return result

    def health_score(self, states):
        score = 100
        penalties = []
        for name, state in states.items():
            if not state["available"]:
                score -= 12
                penalties.append(f"{name} status unavailable")
            elif not str(state.get("status") or "").endswith(("ready", "READY")):
                score -= 5
                penalties.append(f"{name} not reporting ready")

        enterprise = states.get("enterprise", {}).get("data", {})
        kpis = enterprise.get("kpis", {})
        if int(kpis.get("paid_orders", 0) or 0) == 0:
            score -= 15
            penalties.append("no verified paid orders")
        if int(kpis.get("customers", 0) or 0) == 0:
            score -= 8
            penalties.append("no customer records")
        if int(kpis.get("products", 0) or 0) == 0:
            score -= 20
            penalties.append("no active products")

        return {
            "score": max(0, min(100, score)),
            "rating": (
                "STRONG" if score >= 85
                else "STABLE" if score >= 70
                else "NEEDS_ATTENTION" if score >= 50
                else "CRITICAL"
            ),
            "penalties": penalties,
        }

    def bottlenecks(self, states):
        enterprise = states.get("enterprise", {}).get("data", {})
        kpis = enterprise.get("kpis", {})
        crm = states.get("crm", {}).get("data", {})
        commercial = states.get("commercial", {}).get("data", {})
        issues = []

        if int(kpis.get("paid_orders", 0) or 0) == 0:
            issues.append({
                "severity": "HIGH",
                "area": "sales",
                "issue": "No verified paid orders",
                "recommended_action": "Drive the first real customer acquisition and verify the full checkout flow.",
            })
        if int(kpis.get("customers", 0) or 0) == 0:
            issues.append({
                "severity": "MEDIUM",
                "area": "crm",
                "issue": "No customer profiles",
                "recommended_action": "Capture customer email and order records through checkout.",
            })
        if int(commercial.get("support_drafts", 0) or 0) == 0 and int(crm.get("open_support_tickets", 0) or 0) > 0:
            issues.append({
                "severity": "MEDIUM",
                "area": "support",
                "issue": "Open tickets have no drafted responses",
                "recommended_action": "Refresh Commercial Operations support drafting.",
            })
        if not issues:
            issues.append({
                "severity": "LOW",
                "area": "operations",
                "issue": "No critical bottleneck detected",
                "recommended_action": "Continue measuring conversion and revenue.",
            })
        return issues

    def opportunity_ranking(self, states):
        enterprise = states.get("enterprise", {}).get("data", {})
        ventures = enterprise.get("venture_priorities", []) or []
        ranked = []
        for v in ventures:
            score = float(v.get("priority_score", 0) or 0)
            ranked.append({
                "venture_id": v.get("venture_id"),
                "name": v.get("name"),
                "status": v.get("status"),
                "score": round(score, 2),
                "reason": "Enterprise portfolio priority score",
            })
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked

    def executive_recommendations(self, states, bottlenecks):
        recs = []
        for item in bottlenecks:
            recs.append({
                "priority": item["severity"],
                "area": item["area"],
                "recommendation": item["recommended_action"],
                "execution_status": "RECOMMENDATION_ONLY",
            })

        marketing = states.get("marketing", {}).get("data", {})
        if int(marketing.get("campaigns_ready", 0) or 0) > 0:
            recs.append({
                "priority": "MEDIUM",
                "area": "marketing",
                "recommendation": "Review and approve the highest-priority prepared campaign.",
                "execution_status": "RECOMMENDATION_ONLY",
            })
        return recs[:10]

    def timeline(self, limit=50):
        journal = self.live / "full_autonomy_journal.jsonl"
        if not journal.exists():
            return []
        rows = []
        try:
            with journal.open(encoding="utf-8") as f:
                for line in f:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            return []
        rows.sort(key=lambda x: str(x.get("ts", "")), reverse=True)
        return rows[:limit]

    def run_cycle(self):
        states = self.module_states()
        bottlenecks = self.bottlenecks(states)
        opportunities = self.opportunity_ranking(states)
        state = {
            "status": "executive_intelligence_ready",
            "company_health": self.health_score(states),
            "modules": {
                name: {
                    "available": data["available"],
                    "status": data["status"],
                    "updated_at": data["updated_at"],
                }
                for name, data in states.items()
            },
            "bottlenecks": bottlenecks,
            "opportunities": opportunities,
            "recommendations": self.executive_recommendations(states, bottlenecks),
            "timeline_events": len(self.timeline()),
            "top_opportunity": opportunities[0]["name"] if opportunities else None,
            "external_actions_enabled": False,
            "dashboard_url": "http://127.0.0.1:8778",
            "updated_at": now(),
        }
        write_json(self.live / "executive_intelligence_v16_live.json", state)
        write_json(self.records / "executive_snapshot_latest.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "executive_intelligence_v16_cycle",
            "event_type": "executive_intelligence_v16_cycle",
            "state": state,
        })
        return state
