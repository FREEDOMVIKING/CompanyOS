
import json
import os
import tempfile
from collections import Counter
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

def read_jsonl(path, limit=1000):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        return []
    return rows[-limit:]

class SelfImprovementLearningV23:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/self_improvement_learning_v23_850001_900000"
        self.records = self.home / "learning_records_v23"
        self.knowledge = self.records / "organizational_knowledge.json"
        self.lessons_log = self.records / "lessons.jsonl"
        self.proposals = self.records / "improvement_proposals.json"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def source_paths(self):
        return {
            "revenue": self.live / "autonomous_revenue_v11_live.json",
            "marketing": self.live / "autonomous_sales_marketing_v12_live.json",
            "crm": self.live / "customer_growth_crm_v13_live.json",
            "commercial": self.live / "commercial_operations_v14_live.json",
            "enterprise": self.live / "enterprise_automation_v15_live.json",
            "executive": self.live / "executive_intelligence_v16_live.json",
            "operations": self.live / "autonomous_operations_v17_live.json",
            "launcher": self.live / "external_venture_launcher_v19_live.json",
            "validation": self.live / "validation_launch_director_v20_live.json",
            "opportunity": self.live / "opportunity_intelligence_v21_live.json",
            "research": self.live / "autonomous_research_network_v22_live.json",
        }

    def collect_sources(self):
        return {name: read_json(path, {}) for name, path in self.source_paths().items()}

    def learn_revenue(self, sources):
        enterprise = sources.get("enterprise", {})
        kpis = enterprise.get("kpis", {})
        revenue = float(kpis.get("revenue_usd", 0) or 0)
        paid_orders = int(kpis.get("paid_orders", 0) or 0)
        products = int(kpis.get("products", 0) or 0)
        lessons = []
        if paid_orders == 0:
            lessons.append({
                "category": "revenue",
                "lesson": "No verified paid orders exist yet, so pricing and conversion assumptions remain unvalidated.",
                "confidence": 0.95,
                "evidence": {"paid_orders": paid_orders, "revenue_usd": revenue},
            })
        elif products > 0:
            lessons.append({
                "category": "revenue",
                "lesson": "Verified sales exist and can now inform product prioritization.",
                "confidence": 0.9,
                "evidence": {"paid_orders": paid_orders, "products": products, "revenue_usd": revenue},
            })
        return lessons

    def learn_validation(self, sources):
        validation = sources.get("validation", {})
        lessons = []
        blockers = []
        for item in validation.get("results", []) or []:
            blockers.extend(item.get("blockers", []) or [])
        counts = Counter(blockers)
        for blocker, count in counts.most_common():
            lessons.append({
                "category": "validation",
                "lesson": f"Repeated blocker detected: {blocker}",
                "confidence": min(0.95, 0.6 + count * 0.1),
                "evidence": {"occurrences": count},
            })
        if validation.get("ready_for_launch_review", 0):
            lessons.append({
                "category": "validation",
                "lesson": "At least one venture passed the internal launch-readiness threshold.",
                "confidence": 0.9,
                "evidence": {"ready_for_launch_review": validation.get("ready_for_launch_review")},
            })
        return lessons

    def learn_research(self, sources):
        research = sources.get("research", {})
        lessons = []
        if research and not research.get("network_enabled"):
            lessons.append({
                "category": "research",
                "lesson": "External research is not enabled; current opportunity confidence is primarily internal.",
                "confidence": 1.0,
                "evidence": {
                    "network_enabled": False,
                    "evidence_items": research.get("evidence_items", 0),
                },
            })
        elif research.get("evidence_items", 0):
            lessons.append({
                "category": "research",
                "lesson": "External evidence is available and should be weighted alongside internal venture evidence.",
                "confidence": 0.85,
                "evidence": {"evidence_items": research.get("evidence_items")},
            })
        return lessons

    def learn_operations(self, sources):
        operations = sources.get("operations", {})
        lessons = []
        if operations:
            health = int(operations.get("operations_health_score", 0) or 0)
            if health == 100:
                lessons.append({
                    "category": "operations",
                    "lesson": "Tracked local services are operating without detected failures.",
                    "confidence": 0.95,
                    "evidence": {"operations_health_score": health},
                })
            for item in operations.get("recovery_candidates", []) or []:
                lessons.append({
                    "category": "operations",
                    "lesson": f"Service recovery review required for {item.get('service')}.",
                    "confidence": 0.9,
                    "evidence": item,
                })
        return lessons

    def pricing_recommendations(self, sources):
        validation = sources.get("validation", {})
        recs = []
        for item in validation.get("results", []) or []:
            recs.append({
                "venture_id": item.get("venture_id"),
                "name": item.get("name"),
                "recommended_price_usd": item.get("recommended_price_usd"),
                "basis": "current internal validation evidence",
                "confidence": 0.55 if item.get("state") != "READY_FOR_LAUNCH_REVIEW" else 0.7,
                "requires_real_sales_validation": True,
            })
        return recs

    def scoring_adjustments(self, sources):
        research = sources.get("research", {})
        enterprise = sources.get("enterprise", {})
        kpis = enterprise.get("kpis", {})
        adjustments = []
        if int(kpis.get("paid_orders", 0) or 0) == 0:
            adjustments.append({
                "rule": "reduce_confidence_without_sales",
                "adjustment": -10,
                "reason": "No verified paid orders",
                "apply_automatically": False,
            })
        if not research.get("network_enabled", False):
            adjustments.append({
                "rule": "cap_external_market_confidence",
                "adjustment": "cap_at_70",
                "reason": "No connected external research network",
                "apply_automatically": False,
            })
        return adjustments

    def improvement_proposals(self, lessons, sources):
        proposals = []
        lesson_text = " ".join(x["lesson"].lower() for x in lessons)
        if "no verified paid orders" in lesson_text:
            proposals.append({
                "proposal_id": "first-sale-feedback-loop",
                "title": "Prioritize first verified sale feedback loop",
                "priority": 100,
                "change_type": "workflow",
                "description": "Route the first verified order into pricing, offer, and fulfillment learning.",
                "status": "REVIEW_REQUIRED",
                "automatic_code_change": False,
            })
        if "external research is not enabled" in lesson_text:
            proposals.append({
                "proposal_id": "connect-approved-research-sources",
                "title": "Connect approved research sources",
                "priority": 85,
                "change_type": "configuration",
                "description": "Add approved RSS, JSON, or local evidence sources to V22.",
                "status": "REVIEW_REQUIRED",
                "automatic_code_change": False,
            })
        if sources.get("operations", {}).get("operations_health_score") == 100:
            proposals.append({
                "proposal_id": "preserve-direct-controllers",
                "title": "Preserve direct service controllers",
                "priority": 70,
                "change_type": "operations_policy",
                "description": "Continue avoiding unnecessary full-stack restarts on Termux.",
                "status": "RECOMMENDED",
                "automatic_code_change": False,
            })
        return sorted(proposals, key=lambda x: x["priority"], reverse=True)

    def knowledge_summary(self, lessons, sources):
        categories = Counter(x["category"] for x in lessons)
        return {
            "lessons_total": len(lessons),
            "categories": dict(categories),
            "highest_confidence_lessons": sorted(
                lessons, key=lambda x: x.get("confidence", 0), reverse=True
            )[:10],
            "last_updated": now(),
        }

    def run_cycle(self):
        sources = self.collect_sources()
        lessons = []
        lessons.extend(self.learn_revenue(sources))
        lessons.extend(self.learn_validation(sources))
        lessons.extend(self.learn_research(sources))
        lessons.extend(self.learn_operations(sources))

        for lesson in lessons:
            append_jsonl(self.lessons_log, {"ts": now(), **lesson})

        knowledge = self.knowledge_summary(lessons, sources)
        pricing = self.pricing_recommendations(sources)
        adjustments = self.scoring_adjustments(sources)
        proposals = self.improvement_proposals(lessons, sources)

        state = {
            "status": "self_improvement_learning_ready",
            "lessons_generated": len(lessons),
            "knowledge_categories": knowledge["categories"],
            "pricing_recommendations": pricing,
            "scoring_adjustments": adjustments,
            "improvement_proposals": proposals,
            "automatic_code_changes_enabled": False,
            "external_actions_enabled": False,
            "dashboard_url": "http://127.0.0.1:8785",
            "updated_at": now(),
        }

        write_json(self.knowledge, knowledge)
        write_json(self.proposals, {"proposals": proposals, "updated_at": now()})
        write_json(self.runtime / "learning_state.json", state)
        write_json(self.live / "self_improvement_learning_v23_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "self_improvement_learning_v23_cycle",
            "event_type": "self_improvement_learning_v23_cycle",
            "state": state,
        })
        return state
