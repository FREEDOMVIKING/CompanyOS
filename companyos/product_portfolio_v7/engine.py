import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-") or "product"

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
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def append_jsonl(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, sort_keys=True, default=str) + "\n")

class ProductPortfolioEngineV7:
    def __init__(self, home):
        self.home = Path(home)
        self.runtime = self.home / "companyos_runtime" / "product_portfolio_v7_165001_190000"
        self.live = self.home / ".companyos_runtime"
        self.products = self.home / "generated_products_v7"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.live.mkdir(parents=True, exist_ok=True)
        self.products.mkdir(parents=True, exist_ok=True)

    def catalog(self):
        return [
            {
                "id": "construction-estimate-kit",
                "name": "Construction Estimate Kit",
                "customer": "small concrete and construction contractors",
                "problem": "Job estimating is slow and inconsistent.",
                "offer": "Estimate, labor, materials, proposal, and job-review templates.",
                "demand": 9, "margin": 10, "speed": 9, "competition": 5, "repeatability": 9,
                "base_price": 49,
            },
            {
                "id": "small-business-ops-pack",
                "name": "Small Business Operations Pack",
                "customer": "small business owners",
                "problem": "Daily operations lack repeatable systems.",
                "offer": "Operations, customer follow-up, pricing, and weekly-review templates.",
                "demand": 8, "margin": 10, "speed": 10, "competition": 6, "repeatability": 10,
                "base_price": 39,
            },
            {
                "id": "ai-sales-prompt-system",
                "name": "AI Sales Prompt System",
                "customer": "small business owners using AI",
                "problem": "AI sales outputs are inconsistent and generic.",
                "offer": "A structured prompt system for leads, follow-up, proposals, and objections.",
                "demand": 8, "margin": 10, "speed": 10, "competition": 8, "repeatability": 8,
                "base_price": 29,
            },
            {
                "id": "customer-service-response-library",
                "name": "Customer Service Response Library",
                "customer": "service businesses",
                "problem": "Customer messages are answered inconsistently.",
                "offer": "Ready-to-customize responses for common service scenarios.",
                "demand": 7, "margin": 10, "speed": 10, "competition": 6, "repeatability": 9,
                "base_price": 24,
            },
        ]

    def score(self, item):
        raw = (
            item["demand"] * 0.28 +
            item["margin"] * 0.22 +
            item["speed"] * 0.20 +
            item["repeatability"] * 0.18 +
            (11 - item["competition"]) * 0.12
        )
        return round(raw * 10, 2)

    def optimize_price(self, item):
        score = self.score(item)
        price = item["base_price"]
        if score >= 90:
            price += 20
        elif score >= 82:
            price += 10
        return {
            "starter": max(9, price - 20),
            "standard": price,
            "premium": price + 40,
            "recommended": price,
        }

    def build_templates(self, product_dir, item):
        product = product_dir / "product"
        product.mkdir(parents=True, exist_ok=True)
        templates = {
            "construction-estimate-kit": {
                "estimate_template.csv": "Item,Quantity,Unit,Unit Cost,Labor Hours,Labor Rate,Markup %,Total\nConcrete,1,yd3,0,0,0,20,0\n",
                "proposal_template.md": "# Proposal\n\n## Scope\n\n## Materials\n\n## Labor\n\n## Exclusions\n\n## Price\n\n## Acceptance\n",
                "job_cost_review.md": "# Job Cost Review\n\n## Estimated cost\n\n## Actual cost\n\n## Variance\n\n## Lessons learned\n",
            },
            "small-business-ops-pack": {
                "weekly_review.md": "# Weekly Review\n\n## Revenue\n\n## Wins\n\n## Problems\n\n## Customer issues\n\n## Priorities\n",
                "customer_follow_up.md": "# Customer Follow-up\n\n## New lead\n\n## Quote follow-up\n\n## Post-sale check-in\n",
                "simple_pricing.csv": "Service,Cost,Markup %,Price\nExample,100,25,125\n",
            },
            "ai-sales-prompt-system": {
                "lead_qualification_prompts.md": "# Lead Qualification Prompts\n\nUse these prompts to identify budget, urgency, fit, and decision authority.\n",
                "proposal_prompts.md": "# Proposal Prompts\n\nGenerate a clear scope, exclusions, timeline, and next step.\n",
                "objection_prompts.md": "# Objection Handling Prompts\n\nAddress price, timing, trust, and competitor objections.\n",
            },
            "customer-service-response-library": {
                "response_library.md": "# Response Library\n\n## Delayed service\n\n## Refund request\n\n## Scheduling issue\n\n## Positive review follow-up\n",
                "tone_guide.md": "# Tone Guide\n\nBe clear, calm, specific, and action-oriented.\n",
            },
        }
        for name, content in templates[item["id"]].items():
            (product / name).write_text(content, encoding="utf-8")

    def build_product(self, item):
        product_dir = self.products / slugify(item["name"])
        for folder in ["product", "website", "marketing", "sales", "feedback", "review", "tests"]:
            (product_dir / folder).mkdir(parents=True, exist_ok=True)

        pricing = self.optimize_price(item)
        self.build_templates(product_dir, item)

        (product_dir / "product" / "quick_start.md").write_text(
            f"# Quick Start — {item['name']}\n\n"
            "1. Review each included file.\n"
            "2. Replace example text and numbers.\n"
            "3. Save a clean master copy.\n"
            "4. Test the workflow before customer use.\n",
            encoding="utf-8",
        )

        (product_dir / "sales" / "product_page_copy.md").write_text(
            f"# {item['name']}\n\n"
            f"{item['offer']}\n\n"
            f"Built for {item['customer']}.\n\n"
            f"Recommended price: ${pricing['recommended']}\n",
            encoding="utf-8",
        )

        (product_dir / "marketing" / "email_campaign.md").write_text(
            f"# Email Campaign — {item['name']}\n\n"
            "## Email 1: Problem\n"
            f"{item['problem']}\n\n"
            "## Email 2: Solution\n"
            f"{item['offer']}\n\n"
            "## Email 3: Call to action\n"
            "Review the product and decide whether it fits your workflow.\n",
            encoding="utf-8",
        )

        (product_dir / "marketing" / "social_posts.md").write_text(
            f"# Social Posts\n\n"
            f"1. Stop rebuilding the same process from scratch. {item['name']} gives you a reusable system.\n\n"
            f"2. Built for {item['customer']} who need faster, more consistent work.\n\n"
            f"3. A practical product, not another vague guide.\n",
            encoding="utf-8",
        )

        write_json(product_dir / "marketing" / "seo.json", {
            "title": item["name"],
            "description": item["offer"],
            "keywords": [
                slugify(item["name"]).replace("-", " "),
                "business templates",
                "digital product",
                "small business tools",
            ],
        })

        (product_dir / "feedback" / "customer_feedback.jsonl").touch()
        write_json(product_dir / "feedback" / "feedback_schema.json", {
            "fields": ["rating", "problem_solved", "missing_feature", "refund_requested", "comment"],
            "status": "ready",
        })

        (product_dir / "review" / "marketplace_publish_request.json").write_text(
            json.dumps({
                "state": "AWAITING_OWNER_REVIEW",
                "marketplaces": [],
                "payment_provider": None,
                "publish_enabled": False,
                "price": pricing["recommended"],
            }, indent=2),
            encoding="utf-8",
        )

        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{item['name']}</title>
<style>
body{{font-family:system-ui;margin:0;background:#0b1020;color:#eef2ff}}
main{{max-width:900px;margin:auto;padding:48px 24px}}
.card{{background:#151d33;border-radius:18px;padding:26px;margin:20px 0}}
.price{{font-size:2rem;font-weight:800}}
button{{padding:13px 18px;border-radius:12px;border:0;font-weight:800}}
</style></head>
<body><main>
<h1>{item['name']}</h1>
<section class="card"><h2>{item['offer']}</h2><p>{item['problem']}</p>
<p class="price">${pricing['recommended']}</p>
<button disabled>Checkout pending owner review</button></section>
<section class="card"><h2>Designed for</h2><p>{item['customer']}</p></section>
</main></body></html>"""
        (product_dir / "website" / "index.html").write_text(html, encoding="utf-8")

        write_json(product_dir / "product_manifest.json", {
            "product_id": item["id"],
            "name": item["name"],
            "score": self.score(item),
            "pricing": pricing,
            "status": "BUILT",
            "external_publish": False,
            "generated_at": now(),
        })

        test_code = """import unittest
from pathlib import Path
class ProductTest(unittest.TestCase):
    def test_required_assets(self):
        root=Path(__file__).resolve().parents[1]
        required=[
            root/'product_manifest.json',
            root/'website'/'index.html',
            root/'sales'/'product_page_copy.md',
            root/'marketing'/'email_campaign.md',
            root/'marketing'/'social_posts.md',
            root/'feedback'/'feedback_schema.json',
            root/'review'/'marketplace_publish_request.json',
        ]
        for p in required:self.assertTrue(p.exists(),str(p))
if __name__=='__main__':unittest.main()
"""
        (product_dir / "tests" / "test_product.py").write_text(test_code, encoding="utf-8")

        cp = subprocess.run(
            ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=product_dir,
            text=True,
            capture_output=True,
            timeout=60,
        )

        state = "READY_FOR_MARKETPLACE_REVIEW" if cp.returncode == 0 else "QUALITY_REVIEW_REQUIRED"
        validation = {
            "passed": cp.returncode == 0,
            "state": state,
            "stdout": cp.stdout[-3000:],
            "stderr": cp.stderr[-3000:],
            "validated_at": now(),
        }
        write_json(product_dir / "validation_report.json", validation)
        return {
            "product_id": item["id"],
            "name": item["name"],
            "score": self.score(item),
            "pricing": pricing,
            "workspace": str(product_dir),
            "state": state,
            "quality_passed": cp.returncode == 0,
        }

    def run(self):
        ranked = []
        for item in self.catalog():
            ranked.append({**item, "score": self.score(item)})
        ranked.sort(key=lambda x: x["score"], reverse=True)

        selected = ranked[:3]
        built = [self.build_product(item) for item in selected]

        queue = {
            "items": [
                {
                    "product_id": p["product_id"],
                    "name": p["name"],
                    "workspace": p["workspace"],
                    "state": p["state"],
                    "recommended_price": p["pricing"]["recommended"],
                    "publish_enabled": False,
                    "queued_at": now(),
                }
                for p in built
            ]
        }
        write_json(self.runtime / "marketplace_review_queue.json", queue)

        analytics = {
            "products_built": len(built),
            "products_quality_passed": sum(1 for p in built if p["quality_passed"]),
            "portfolio_value_at_recommended_price": sum(p["pricing"]["recommended"] for p in built),
            "sales_count": 0,
            "revenue_usd": 0.0,
            "refunds": 0,
            "conversion_rate": 0.0,
            "updated_at": now(),
        }
        write_json(self.runtime / "revenue_analytics.json", analytics)

        live = {
            "status": "portfolio_ready_for_review",
            "portfolio_size": len(built),
            "selected_products": built,
            "marketplace_review_queue_length": len(queue["items"]),
            "external_publish": False,
            "payment_connected": False,
            "analytics": analytics,
            "updated_at": now(),
        }
        write_json(self.live / "product_portfolio_v7_live.json", live)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "product_portfolio_ready_for_review",
            "event_type": "product_portfolio_ready_for_review",
            "state": live,
        })
        return live
