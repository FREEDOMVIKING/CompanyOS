import json
import os
import re
import shutil
import subprocess
import tempfile
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

def slugify(value):
    value = str(value or "product").strip().lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "product"

class RevenueEngineV6:
    def __init__(self, home):
        self.home = Path(home)
        self.runtime = self.home / "companyos_runtime" / "revenue_engine_v6_140001_165000"
        self.live_dir = self.home / ".companyos_runtime"
        self.products = self.home / "generated_products"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.live_dir.mkdir(parents=True, exist_ok=True)
        self.products.mkdir(parents=True, exist_ok=True)

    def candidate_catalog(self):
        return [
            {
                "id": "digital-template-business",
                "name": "Digital Template Business",
                "type": "digital_product",
                "customer": "small businesses and independent professionals",
                "problem": "Creating polished business documents repeatedly wastes time.",
                "offer": "A practical business operations template bundle.",
                "startup_cost": 1,
                "build_speed": 10,
                "margin": 10,
                "repeatability": 9,
                "competition": 6,
                "demand": 8,
                "first_sale_speed": 9,
            },
            {
                "id": "construction-estimate-kit",
                "name": "Construction Estimate Kit",
                "type": "digital_product",
                "customer": "small concrete and construction contractors",
                "problem": "Estimating jobs consistently is slow and error-prone.",
                "offer": "A contractor estimate, materials, labor, and proposal toolkit.",
                "startup_cost": 1,
                "build_speed": 9,
                "margin": 10,
                "repeatability": 9,
                "competition": 5,
                "demand": 8,
                "first_sale_speed": 8,
            },
            {
                "id": "ai-prompt-operations-pack",
                "name": "AI Operations Prompt Pack",
                "type": "digital_product",
                "customer": "small business owners adopting AI",
                "problem": "Owners struggle to get reliable business outputs from AI tools.",
                "offer": "A curated prompt system for operations, sales, and customer service.",
                "startup_cost": 1,
                "build_speed": 10,
                "margin": 10,
                "repeatability": 8,
                "competition": 8,
                "demand": 7,
                "first_sale_speed": 8,
            },
        ]

    def score_candidate(self, c):
        upside = (
            c["demand"] * 0.24 +
            c["margin"] * 0.20 +
            c["build_speed"] * 0.18 +
            c["first_sale_speed"] * 0.16 +
            c["repeatability"] * 0.12 +
            (11 - c["startup_cost"]) * 0.06 +
            (11 - c["competition"]) * 0.04
        )
        return round(upside * 10, 2)

    def select_opportunity(self):
        candidates = []
        for c in self.candidate_catalog():
            item = dict(c)
            item["revenue_score"] = self.score_candidate(c)
            candidates.append(item)
        candidates.sort(key=lambda x: x["revenue_score"], reverse=True)
        result = {
            "status": "selected",
            "selected": candidates[0],
            "candidates": candidates,
            "selected_at": now(),
        }
        write_json(self.runtime / "opportunity_selection.json", result)
        return result

    def build_product_spec(self, selected):
        product_name = selected["name"]
        spec = {
            "product_id": selected["id"],
            "product_name": product_name,
            "product_type": selected["type"],
            "customer": selected["customer"],
            "problem": selected["problem"],
            "offer": selected["offer"],
            "price_options": [19, 39, 79],
            "recommended_price": 39,
            "deliverables": [
                "customer-ready product files",
                "quick-start guide",
                "usage instructions",
                "license summary",
                "landing page",
                "marketing copy",
                "launch checklist",
            ],
            "acceptance_criteria": [
                "all product files exist",
                "landing page renders",
                "customer guide exists",
                "marketing assets exist",
                "internal tests pass",
                "external launch remains review-gated",
            ],
            "external_launch": "approval_required",
            "generated_at": now(),
        }
        write_json(self.runtime / "product_specification.json", spec)
        return spec

    def build_digital_template_product(self, workspace, spec):
        templates = workspace / "product" / "templates"
        docs = workspace / "product" / "docs"
        templates.mkdir(parents=True, exist_ok=True)
        docs.mkdir(parents=True, exist_ok=True)

        (templates / "project_intake_form.md").write_text(
            "# Project Intake Form\n\n"
            "## Customer\n\n"
            "## Project goal\n\n"
            "## Scope\n\n"
            "## Deliverables\n\n"
            "## Deadline\n\n"
            "## Budget\n\n"
            "## Approval owner\n",
            encoding="utf-8",
        )
        (templates / "weekly_operations_review.md").write_text(
            "# Weekly Operations Review\n\n"
            "## Wins\n\n"
            "## Problems\n\n"
            "## Revenue activity\n\n"
            "## Customer issues\n\n"
            "## Priorities for next week\n\n"
            "## Decisions required\n",
            encoding="utf-8",
        )
        (templates / "customer_follow_up_messages.md").write_text(
            "# Customer Follow-up Messages\n\n"
            "## New lead\n"
            "Thanks for reaching out. I reviewed your request and the next step is...\n\n"
            "## Quote follow-up\n"
            "I wanted to follow up on the quote and answer any questions...\n\n"
            "## Post-purchase check-in\n"
            "I am checking in to make sure everything is working as expected...\n",
            encoding="utf-8",
        )
        (templates / "simple_pricing_calculator.csv").write_text(
            "Item,Quantity,Unit Cost,Markup %,Total\n"
            "Example service,1,100,25,125\n",
            encoding="utf-8",
        )
        (templates / "business_launch_checklist.md").write_text(
            "# Business Launch Checklist\n\n"
            "- [ ] Offer defined\n"
            "- [ ] Target customer defined\n"
            "- [ ] Price confirmed\n"
            "- [ ] Payment provider configured\n"
            "- [ ] Landing page reviewed\n"
            "- [ ] Customer support process ready\n"
            "- [ ] External launch approved\n",
            encoding="utf-8",
        )
        (docs / "quick_start.md").write_text(
            f"# Quick Start — {spec['product_name']}\n\n"
            "1. Copy the included templates into your preferred document system.\n"
            "2. Replace example text with your business details.\n"
            "3. Use the weekly review every seven days.\n"
            "4. Update pricing before sending customer proposals.\n",
            encoding="utf-8",
        )
        (docs / "license_summary.md").write_text(
            "# License Summary\n\n"
            "This generated package is prepared for owner review. "
            "Define the final customer license before public sale.\n",
            encoding="utf-8",
        )

    def build_product(self, spec):
        workspace = self.products / slugify(spec["product_name"])
        if workspace.exists():
            archive = self.products / "_archive"
            archive.mkdir(parents=True, exist_ok=True)
            backup = archive / f"{workspace.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            shutil.copytree(workspace, backup)
        for folder in ["product", "sales", "marketing", "website", "tests", "review"]:
            (workspace / folder).mkdir(parents=True, exist_ok=True)

        self.build_digital_template_product(workspace, spec)
        write_json(workspace / "product_specification.json", spec)

        landing = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{spec['product_name']}</title>
<style>
body{{font-family:system-ui;margin:0;background:#0b1020;color:#eef2ff}}
main{{max-width:940px;margin:auto;padding:48px 22px}}
.hero,.card{{background:#151d33;border-radius:20px;padding:28px;margin:20px 0}}
.price{{font-size:2rem;font-weight:800}}
button{{padding:14px 20px;border:0;border-radius:12px;font-weight:800}}
small{{color:#aab4cc}}
</style>
</head>
<body>
<main>
<section class="hero">
<h1>{spec['product_name']}</h1>
<h2>{spec['offer']}</h2>
<p>Built for {spec['customer']}.</p>
<p class="price">${spec['recommended_price']}</p>
<button disabled>Checkout connection pending review</button>
<p><small>External payment and publishing require owner approval.</small></p>
</section>
<section class="card">
<h2>What is included</h2>
<ul>
<li>Project intake form</li>
<li>Weekly operations review</li>
<li>Customer follow-up messages</li>
<li>Simple pricing calculator</li>
<li>Business launch checklist</li>
<li>Quick-start guide</li>
</ul>
</section>
<section class="card">
<h2>Why it helps</h2>
<p>{spec['problem']}</p>
</section>
</main>
</body>
</html>"""
        (workspace / "website" / "index.html").write_text(landing, encoding="utf-8")

        (workspace / "sales" / "product_description.md").write_text(
            f"# {spec['product_name']}\n\n"
            f"{spec['offer']}\n\n"
            f"Designed for {spec['customer']}.\n\n"
            "## Included\n"
            "- Practical business templates\n"
            "- Quick-start instructions\n"
            "- Reusable customer communication examples\n"
            "- Pricing and launch support files\n",
            encoding="utf-8",
        )
        (workspace / "sales" / "checkout_configuration.json").write_text(
            json.dumps({
                "status": "not_connected",
                "recommended_price_usd": spec["recommended_price"],
                "approval_required": True,
                "payment_provider": None,
            }, indent=2),
            encoding="utf-8",
        )
        (workspace / "marketing" / "launch_copy.md").write_text(
            f"# Launch Copy\n\n"
            f"## Headline\nSave hours with the {spec['product_name']}.\n\n"
            f"## Short description\n{spec['offer']}\n\n"
            "## Social post\n"
            "Stop rebuilding the same business documents from scratch. "
            "This ready-to-use template bundle helps small businesses organize work, "
            "follow up with customers, and operate more consistently.\n\n"
            "## Email subject lines\n"
            "- A simpler way to organize your business\n"
            "- Stop rebuilding the same documents\n"
            "- Your small-business operations starter kit\n",
            encoding="utf-8",
        )
        (workspace / "marketing" / "seo.json").write_text(
            json.dumps({
                "title": spec["product_name"],
                "description": spec["offer"],
                "keywords": [
                    "small business templates",
                    "operations templates",
                    "business document bundle",
                    "customer follow up template",
                ],
            }, indent=2),
            encoding="utf-8",
        )
        (workspace / "review" / "external_launch_checklist.md").write_text(
            "# External Launch Review\n\n"
            "- [ ] Product quality approved\n"
            "- [ ] Price approved\n"
            "- [ ] License approved\n"
            "- [ ] Payment provider connected\n"
            "- [ ] Refund policy added\n"
            "- [ ] Privacy policy added if collecting customer data\n"
            "- [ ] Domain or storefront approved\n"
            "- [ ] Final publish approved\n",
            encoding="utf-8",
        )

        test_code = """import unittest
from pathlib import Path

class RevenueProductTests(unittest.TestCase):
    def test_required_files(self):
        root=Path(__file__).resolve().parents[1]
        required=[
            root/'website'/'index.html',
            root/'sales'/'product_description.md',
            root/'marketing'/'launch_copy.md',
            root/'product'/'docs'/'quick_start.md',
            root/'review'/'external_launch_checklist.md',
            root/'product_specification.json',
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))

if __name__=='__main__':
    unittest.main()
"""
        (workspace / "tests" / "test_product.py").write_text(test_code, encoding="utf-8")
        return workspace

    def validate_product(self, workspace):
        cp = subprocess.run(
            ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=str(workspace),
            text=True,
            capture_output=True,
            timeout=60,
        )
        checks = {
            "product_directory": (workspace / "product").exists(),
            "landing_page": (workspace / "website" / "index.html").exists(),
            "sales_copy": (workspace / "sales" / "product_description.md").exists(),
            "marketing_copy": (workspace / "marketing" / "launch_copy.md").exists(),
            "quick_start": (workspace / "product" / "docs" / "quick_start.md").exists(),
            "launch_review": (workspace / "review" / "external_launch_checklist.md").exists(),
            "tests_passed": cp.returncode == 0,
        }
        result = {
            "passed": all(checks.values()),
            "checks": checks,
            "stdout": cp.stdout[-4000:],
            "stderr": cp.stderr[-4000:],
            "validated_at": now(),
        }
        write_json(workspace / "validation_report.json", result)
        return result

    def queue_for_review(self, workspace, spec, validation):
        queue_file = self.runtime / "launch_review_queue.json"
        queue = read_json(queue_file, {"items": []})
        product_id = spec["product_id"]
        existing = next((i for i in queue["items"] if i.get("product_id") == product_id), None)
        item = {
            "product_id": product_id,
            "product_name": spec["product_name"],
            "workspace": str(workspace),
            "recommended_price_usd": spec["recommended_price"],
            "state": "READY_FOR_EXTERNAL_REVIEW" if validation["passed"] else "QUALITY_REVIEW_REQUIRED",
            "external_publish": False,
            "payment_connected": False,
            "queued_at": now(),
        }
        if existing:
            existing.update(item)
        else:
            queue["items"].append(item)
        write_json(queue_file, queue)
        return queue

    def run(self):
        opportunity = self.select_opportunity()
        selected = opportunity["selected"]
        spec = self.build_product_spec(selected)
        workspace = self.build_product(spec)
        validation = self.validate_product(workspace)
        queue = self.queue_for_review(workspace, spec, validation)

        state = {
            "status": "ready_for_external_review" if validation["passed"] else "quality_review_required",
            "product_id": spec["product_id"],
            "product_name": spec["product_name"],
            "revenue_score": selected["revenue_score"],
            "recommended_price_usd": spec["recommended_price"],
            "workspace": str(workspace),
            "quality_passed": validation["passed"],
            "launch_queue_length": len(queue["items"]),
            "external_publish": False,
            "payment_connected": False,
            "progress_percent": 90 if validation["passed"] else 75,
            "updated_at": now(),
        }
        write_json(self.runtime / "latest_run.json", state)
        write_json(self.live_dir / "revenue_engine_v6_live.json", state)
        append_jsonl(
            self.live_dir / "full_autonomy_journal.jsonl",
            {
                "ts": now(),
                "event": "revenue_product_ready_for_review" if validation["passed"] else "revenue_product_quality_failed",
                "event_type": "revenue_product_ready_for_review" if validation["passed"] else "revenue_product_quality_failed",
                "state": state,
            },
        )
        return {
            "status": state["status"],
            "state": state,
            "opportunity": opportunity,
            "validation": validation,
        }
