
import csv
import json
import os
import re
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

def slugify(value):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(value).lower())).strip("-")

class AutonomousProductBuilderV28:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_product_builder_v28_1100001_1150000"
        self.products = self.home / "generated_products_v28"
        self.records = self.home / "product_builder_records_v28"
        self.approved = self.live / "approved_opportunities.json"
        for p in (self.live, self.runtime, self.products, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def opportunities(self):
        data = read_json(self.approved, {})
        items = data.get("opportunities", []) or []
        selected = []
        for item in items:
            score = float(item.get("score", 0) or 0)
            status = str(item.get("status", "")).upper()
            if status in {
                "APPROVED", "READY", "SELECTED", "APPROVED_INTERNAL",
                "DISCOVERED_REVIEW_REQUIRED"
            } and score >= 60:
                selected.append(item)

        if not selected:
            launcher = read_json(self.live / "external_venture_launcher_v19_live.json", {})
            top = launcher.get("top_venture")
            if top:
                selected.append({
                    "opportunity_id": slugify(top),
                    "name": top,
                    "score": 75,
                    "status": "APPROVED_INTERNAL",
                    "summary": "Imported from the active CompanyOS venture portfolio."
                })
        return selected

    def product_type(self, name, summary):
        text = f"{name} {summary}".lower()
        if any(x in text for x in ("estimate", "calculator", "pricing", "cost")):
            return "calculator_and_template_kit"
        if any(x in text for x in ("response", "customer", "support", "email")):
            return "response_library"
        if any(x in text for x in ("automation", "operations", "workflow")):
            return "operations_toolkit"
        return "digital_template_bundle"

    def pricing(self, score):
        if score >= 90:
            return {"starter": 39, "standard": 69, "premium": 119, "recommended": 69}
        if score >= 75:
            return {"starter": 29, "standard": 49, "premium": 89, "recommended": 49}
        return {"starter": 19, "standard": 39, "premium": 69, "recommended": 39}

    def write_csv_tool(self, path, product_type):
        rows = []
        if product_type == "calculator_and_template_kit":
            rows = [
                ["Item", "Quantity", "Unit Cost", "Line Total"],
                ["Example labor", "1", "0", "=B2*C2"],
                ["Example material", "1", "0", "=B3*C3"],
                ["Subtotal", "", "", "=SUM(D2:D3)"],
                ["Markup %", "", "20", ""],
                ["Total", "", "", "=D4*(1+C5/100)"],
            ]
        elif product_type == "response_library":
            rows = [
                ["Category", "Situation", "Response Template"],
                ["Lead", "New inquiry", "Thanks for reaching out. Here is the next step..."],
                ["Support", "Order question", "I found your order and am reviewing it now..."],
                ["Follow-up", "No reply", "Just checking back to make sure you received..."],
            ]
        else:
            rows = [
                ["Task", "Owner", "Status", "Due Date", "Notes"],
                ["Define offer", "", "Not Started", "", ""],
                ["Prepare assets", "", "Not Started", "", ""],
                ["Quality review", "", "Not Started", "", ""],
                ["Launch review", "", "Not Started", "", ""],
            ]
        with Path(path).open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

    def write_guide(self, path, name, summary, product_type):
        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<style>
body{{font-family:system-ui;max-width:900px;margin:auto;padding:32px;background:#f7f8fb;color:#172033}}
section{{background:white;padding:24px;border-radius:16px;margin:16px 0}}
h1,h2{{line-height:1.15}}
</style></head><body>
<section><h1>{name}</h1><p>{summary or "A practical CompanyOS-generated digital product."}</p></section>
<section><h2>What is included</h2>
<ul>
<li>Editable CSV tool</li>
<li>Quick-start guide</li>
<li>Implementation checklist</li>
<li>License and usage notes</li>
</ul></section>
<section><h2>Product type</h2><p>{product_type}</p></section>
<section><h2>Quick start</h2>
<ol><li>Open the CSV tool.</li><li>Replace the examples with your own information.</li>
<li>Review calculations and wording.</li><li>Save a customer-ready copy.</li></ol></section>
</body></html>"""
        Path(path).write_text(html, encoding="utf-8")

    def quality_score(self, workspace):
        checks = {
            "manifest": (workspace / "product_manifest.json").exists(),
            "csv_tool": (workspace / "editable_tool.csv").exists(),
            "guide": (workspace / "quick_start_guide.html").exists(),
            "readme": (workspace / "README.md").exists(),
            "license": (workspace / "LICENSE.txt").exists(),
            "checklist": (workspace / "quality_checklist.json").exists(),
        }
        score = round(sum(checks.values()) / len(checks) * 100, 2)
        return score, checks

    def build_product(self, opportunity):
        name = opportunity.get("name") or "New Digital Product"
        product_id = slugify(opportunity.get("opportunity_id") or name)
        version = "1.0.0"
        workspace = self.products / product_id / version
        workspace.mkdir(parents=True, exist_ok=True)

        score = float(opportunity.get("score", 0) or 0)
        summary = opportunity.get("summary") or ""
        ptype = self.product_type(name, summary)
        prices = self.pricing(score)

        manifest = {
            "product_id": product_id,
            "name": name,
            "version": version,
            "product_type": ptype,
            "source_opportunity": opportunity,
            "pricing": prices,
            "workspace": str(workspace),
            "state": "BUILDING",
            "external_publish_approved": False,
            "created_at": now(),
        }
        write_json(workspace / "product_manifest.json", manifest)
        self.write_csv_tool(workspace / "editable_tool.csv", ptype)
        self.write_guide(workspace / "quick_start_guide.html", name, summary, ptype)
        (workspace / "README.md").write_text(
            f"# {name}\n\n{summary}\n\nVersion: {version}\n\n"
            "This package was generated locally by CompanyOS V28.\n",
            encoding="utf-8"
        )
        (workspace / "LICENSE.txt").write_text(
            "Internal draft license: review before external sale or distribution.\n",
            encoding="utf-8"
        )
        write_json(workspace / "quality_checklist.json", {
            "items": [
                {"step": "Open CSV and verify formulas", "done": False},
                {"step": "Review all customer-facing language", "done": False},
                {"step": "Confirm pricing", "done": False},
                {"step": "Approve license", "done": False},
                {"step": "Approve external publication", "done": False},
            ]
        })

        quality, checks = self.quality_score(workspace)
        manifest["quality_score"] = quality
        manifest["quality_checks"] = checks
        manifest["state"] = "READY_FOR_PRODUCT_REVIEW" if quality >= 90 else "NEEDS_PRODUCT_REWORK"
        manifest["updated_at"] = now()
        write_json(workspace / "product_manifest.json", manifest)
        return manifest

    def run_cycle(self):
        products = [self.build_product(x) for x in self.opportunities()]
        products.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        storefront_queue = [{
            "product_id": p["product_id"],
            "name": p["name"],
            "version": p["version"],
            "price_usd": p["pricing"]["recommended"],
            "workspace": p["workspace"],
            "status": "STOREFRONT_REVIEW_REQUIRED",
        } for p in products if p["state"] == "READY_FOR_PRODUCT_REVIEW"]

        validation_queue = [{
            "product_id": p["product_id"],
            "name": p["name"],
            "quality_score": p["quality_score"],
            "workspace": p["workspace"],
            "status": "VALIDATION_REQUIRED",
        } for p in products]

        state = {
            "status": "autonomous_product_builder_ready",
            "products_built": len(products),
            "products_ready_for_review": sum(
                p["state"] == "READY_FOR_PRODUCT_REVIEW" for p in products
            ),
            "products": products,
            "storefront_handoff_queue": storefront_queue,
            "validation_handoff_queue": validation_queue,
            "automatic_external_publish_enabled": False,
            "automatic_customer_delivery_enabled": False,
            "dashboard_url": "http://127.0.0.1:8790",
            "updated_at": now(),
        }

        write_json(self.runtime / "product_builder_state.json", state)
        write_json(self.live / "autonomous_product_builder_v28_live.json", state)
        write_json(self.records / "storefront_handoff_queue.json", {
            "products": storefront_queue, "updated_at": now()
        })
        write_json(self.records / "validation_handoff_queue.json", {
            "products": validation_queue, "updated_at": now()
        })
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "autonomous_product_builder_v28_cycle",
            "event_type": "autonomous_product_builder_v28_cycle",
            "state": {
                "products_built": state["products_built"],
                "products_ready_for_review": state["products_ready_for_review"],
            },
        })
        return state
