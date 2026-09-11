
import json, os, tempfile, hashlib
from pathlib import Path
from datetime import datetime, timezone

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
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
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

class AutonomousMarketingAcquisitionV31:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_marketing_acquisition_v31_1250001_1300000"
        self.records = self.home / "marketing_acquisition_records_v31"
        self.metrics_file = self.live / "marketing_metrics_v31.json"
        self.leads_file = self.live / "marketing_leads_v31.json"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)
        if not self.metrics_file.exists():
            write_json(self.metrics_file, {"campaigns": {}})
        if not self.leads_file.exists():
            write_json(self.leads_file, {"leads": []})

    def catalog(self):
        return read_json(
            self.live / "autonomous_storefront_sales_v29_live.json", {}
        ).get("catalog", []) or []

    def portfolio(self):
        return read_json(
            self.live / "autonomous_revenue_expansion_v26_live.json", {}
        ).get("portfolio", []) or []

    def campaign_for(self, product):
        pid = product.get("product_id")
        name = product.get("name")
        price = float(product.get("price_usd", 0) or 0)
        ptype = product.get("product_type") or "digital_product"

        if "template" in ptype:
            audience = "small business owners and operators who need ready-to-use templates"
            channels = ["organic_social", "short_form_video", "search_content", "email"]
            hook = f"Save time with a ready-to-use {name}"
        elif "calculator" in ptype:
            audience = "operators who need faster estimating, pricing, or quoting"
            channels = ["search_content", "industry_forums", "organic_social", "email"]
            hook = f"Build faster, more consistent estimates with {name}"
        else:
            audience = "small business owners looking for practical workflow improvements"
            channels = ["organic_social", "search_content", "email"]
            hook = f"Simplify your workflow with {name}"

        return {
            "campaign_id": hashlib.sha256(f"{pid}|v31".encode()).hexdigest()[:16],
            "product_id": pid,
            "product_name": name,
            "audience_hypothesis": audience,
            "channels": channels,
            "offer_price_usd": price,
            "hook": hook,
            "draft_assets": {
                "headline": hook,
                "short_copy": f"{name} is a practical digital toolkit designed to help {audience}.",
                "cta": "View the product",
                "email_subject": f"A simpler way to use {name}",
            },
            "external_publish_status": "REVIEW_REQUIRED",
            "ad_spend_approved_usd": 0,
        }

    def metrics_for(self, campaign_id):
        data = read_json(self.metrics_file, {"campaigns": {}})
        return data.get("campaigns", {}).get(campaign_id, {
            "visitors": 0, "leads": 0, "orders": 0, "spend_usd": 0
        })

    def score_campaign(self, plan, metrics):
        visitors = int(metrics.get("visitors", 0) or 0)
        leads = int(metrics.get("leads", 0) or 0)
        orders = int(metrics.get("orders", 0) or 0)
        spend = float(metrics.get("spend_usd", 0) or 0)
        price = float(plan.get("offer_price_usd", 0) or 0)

        lead_rate = round(leads / visitors * 100, 2) if visitors else 0.0
        order_rate = round(orders / visitors * 100, 2) if visitors else 0.0
        cac = round(spend / orders, 2) if orders else None
        revenue = round(orders * price, 2)

        score = 50
        if visitors >= 25: score += 10
        if lead_rate >= 5: score += 10
        if order_rate >= 1: score += 15
        if orders > 0 and spend == 0: score += 10
        if cac is not None and price > 0 and cac < price * 0.35: score += 15
        score = min(score, 100)

        return {
            "visitors": visitors,
            "leads": leads,
            "orders": orders,
            "spend_usd": spend,
            "lead_conversion_percent": lead_rate,
            "order_conversion_percent": order_rate,
            "customer_acquisition_cost_usd": cac,
            "attributed_revenue_usd": revenue,
            "campaign_score": score,
        }

    def recommendations(self, plans):
        recs = []
        for row in plans:
            a = row["analytics"]
            if a["visitors"] == 0:
                recs.append({
                    "campaign_id": row["campaign_id"],
                    "priority": 100,
                    "recommendation": "Collect initial traffic and conversion evidence before changing price or message.",
                    "status": "REVIEW_REQUIRED"
                })
            elif a["orders"] == 0 and a["visitors"] >= 25:
                recs.append({
                    "campaign_id": row["campaign_id"],
                    "priority": 95,
                    "recommendation": "Test a new headline, CTA, or offer framing before increasing traffic.",
                    "status": "REVIEW_REQUIRED"
                })
            elif a["orders"] > 0:
                recs.append({
                    "campaign_id": row["campaign_id"],
                    "priority": 85,
                    "recommendation": "Preserve winning message and test one variable at a time.",
                    "status": "RECOMMENDED"
                })
        return sorted(recs, key=lambda x: x["priority"], reverse=True)

    def lead_handoff(self):
        raw = read_json(self.leads_file, {"leads": []}).get("leads", []) or []
        out = []
        for lead in raw:
            score = 0
            score += 40 if lead.get("email") else 0
            score += 30 if lead.get("product_id") else 0
            score += 20 if lead.get("intent") in ("high", "buying", "pricing") else 0
            score += 10 if lead.get("source") else 0
            out.append({
                "lead_id": lead.get("lead_id") or hashlib.sha256(
                    json.dumps(lead, sort_keys=True).encode()
                ).hexdigest()[:16],
                "product_id": lead.get("product_id"),
                "source": lead.get("source"),
                "qualification_score": min(score, 100),
                "status": "CRM_HANDOFF_READY" if score >= 60 else "NURTURE_REVIEW",
                "external_contact_approved": False,
            })
        return out

    def run_cycle(self):
        plans = []
        for product in self.catalog():
            plan = self.campaign_for(product)
            plan["analytics"] = self.score_campaign(
                plan, self.metrics_for(plan["campaign_id"])
            )
            plans.append(plan)

        leads = self.lead_handoff()
        recs = self.recommendations(plans)

        state = {
            "status": "autonomous_marketing_acquisition_ready",
            "campaigns_total": len(plans),
            "leads_total": len(leads),
            "qualified_leads": sum(x["status"] == "CRM_HANDOFF_READY" for x in leads),
            "campaigns": plans,
            "lead_handoff_queue": leads,
            "optimization_recommendations": recs,
            "automatic_posting_enabled": False,
            "automatic_ad_spend_enabled": False,
            "automatic_email_enabled": False,
            "external_marketing_actions_enabled": False,
            "dashboard_url": "http://127.0.0.1:8793",
            "updated_at": now(),
        }

        write_json(self.runtime / "marketing_acquisition_state.json", state)
        write_json(self.live / "autonomous_marketing_acquisition_v31_live.json", state)
        write_json(self.records / "campaign_registry.json", {
            "campaigns": plans, "updated_at": now()
        })
        write_json(self.records / "lead_handoff_queue.json", {
            "leads": leads, "updated_at": now()
        })
        write_json(self.records / "optimization_recommendations.json", {
            "recommendations": recs, "updated_at": now()
        })

        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "autonomous_marketing_acquisition_v31_cycle",
            "event_type": "autonomous_marketing_acquisition_v31_cycle",
            "state": {
                "campaigns_total": len(plans),
                "leads_total": len(leads),
                "qualified_leads": state["qualified_leads"],
            }
        })
        return state
