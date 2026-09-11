import hashlib, json, os, tempfile
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

def make_id(*parts):
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:16]

class CommercialOperationsV14:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/commercial_operations_v14_400001_450000"
        self.storefront = self.home / "companyos_runtime/storefront_sales_v8_190001_220000"
        self.crm = self.home / "companyos_runtime/customer_growth_crm_v13_360001_400000"
        self.marketing = self.home / "companyos_runtime/autonomous_sales_marketing_v12_320001_360000"
        self.records = self.home / "commercial_records_v14"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def catalog(self):
        return read_json(self.storefront / "catalog.json", {"products": []}).get("products", [])

    def orders(self):
        return read_json(self.storefront / "orders.json", {"orders": []}).get("orders", [])

    def customers(self):
        return read_json(self.crm / "crm_index.json", {"customers": {}}).get("customers", {})

    def tickets(self):
        return read_json(self.crm / "support_tickets.json", {"tickets": []}).get("tickets", [])

    def create_quote(self, payload):
        customer = payload.get("customer") or {}
        items = payload.get("items") or []
        subtotal = sum(float(i.get("quantity", 1)) * float(i.get("unit_price", 0)) for i in items)
        discount = max(0.0, min(float(payload.get("discount_percent", 0) or 0), 25.0))
        total = round(subtotal * (1 - discount / 100), 2)
        qid = make_id(customer.get("email"), now(), subtotal)
        quote = {
            "quote_id": qid,
            "customer": customer,
            "items": items,
            "subtotal": round(subtotal, 2),
            "discount_percent": discount,
            "total": total,
            "currency": "USD",
            "status": "DRAFT_REVIEW_REQUIRED",
            "created_at": now(),
        }
        write_json(self.records / "quotes" / f"{qid}.json", quote)
        return quote

    def create_proposal(self, payload):
        title = payload.get("title") or "CompanyOS Proposal"
        problem = payload.get("problem") or "Customer need not yet described."
        solution = payload.get("solution") or "Proposed solution pending review."
        timeline = payload.get("timeline") or "To be agreed."
        price = float(payload.get("price", 0) or 0)
        pid = make_id(title, now())
        proposal = {
            "proposal_id": pid,
            "title": title,
            "executive_summary": f"This proposal addresses: {problem}",
            "solution": solution,
            "scope": payload.get("scope") or [],
            "timeline": timeline,
            "price_usd": price,
            "assumptions": payload.get("assumptions") or [],
            "status": "DRAFT_REVIEW_REQUIRED",
            "created_at": now(),
        }
        write_json(self.records / "proposals" / f"{pid}.json", proposal)
        return proposal

    def create_contract(self, payload):
        cid = make_id(payload.get("customer_name"), now())
        contract = {
            "contract_id": cid,
            "title": payload.get("title") or "Service Agreement Draft",
            "parties": payload.get("parties") or [],
            "scope": payload.get("scope") or [],
            "payment_terms": payload.get("payment_terms") or "Payment terms require review.",
            "delivery_terms": payload.get("delivery_terms") or "Delivery terms require review.",
            "termination": payload.get("termination") or "Termination terms require legal review.",
            "governing_law": payload.get("governing_law") or "Not specified.",
            "legal_review_required": True,
            "status": "DRAFT_ONLY",
            "created_at": now(),
        }
        write_json(self.records / "contracts" / f"{cid}.json", contract)
        return contract

    def create_invoice(self, payload):
        items = payload.get("items") or []
        total = round(sum(float(i.get("quantity", 1)) * float(i.get("unit_price", 0)) for i in items), 2)
        iid = make_id(payload.get("customer_email"), now(), total)
        invoice = {
            "invoice_id": iid,
            "customer_email": payload.get("customer_email"),
            "items": items,
            "total_usd": total,
            "due_date": payload.get("due_date"),
            "payment_method": "crypto_invoice_link_pending",
            "status": "DRAFT_NOT_SENT",
            "created_at": now(),
        }
        write_json(self.records / "invoices" / f"{iid}.json", invoice)
        return invoice

    def support_drafts(self):
        drafts = []
        for ticket in self.tickets():
            tid = ticket.get("ticket_id")
            message = ticket.get("message", "")
            priority = ticket.get("priority", "NORMAL")
            draft = {
                "ticket_id": tid,
                "priority": priority,
                "draft_response": (
                    "We’re sorry you ran into this. We’re reviewing the issue now and will verify "
                    "your order, payment status, and delivery record before proposing the next step."
                    if priority == "HIGH"
                    else
                    "Thanks for reaching out. We’ve received your message and are reviewing the details."
                ),
                "send_status": "REVIEW_REQUIRED",
                "created_at": now(),
            }
            write_json(self.records / "support_drafts" / f"{tid}.json", draft)
            drafts.append(draft)
        return drafts

    def funnel(self):
        orders = self.orders()
        customers = self.customers()
        leads = sum(1 for c in customers.values() if c.get("segment") == "LEAD")
        paying = sum(1 for c in customers.values() if c.get("paid_orders", 0) > 0)
        total_orders = len(orders)
        paid_orders = sum(o.get("status") in ("PAID","FULFILLMENT_READY","DELIVERED") for o in orders)
        return {
            "leads": leads,
            "customers": len(customers),
            "paying_customers": paying,
            "orders": total_orders,
            "paid_orders": paid_orders,
            "lead_to_customer_rate": round((paying / leads) * 100, 2) if leads else 0.0,
            "order_conversion_rate": round((paid_orders / total_orders) * 100, 2) if total_orders else 0.0,
        }

    def ab_tests(self):
        tests = []
        for product in self.catalog():
            pid = product.get("product_id")
            price = float(product.get("pricing", {}).get("recommended", 0) or 0)
            tests.append({
                "test_id": make_id(pid, "headline-price"),
                "product_id": pid,
                "status": "PLANNED_REVIEW_REQUIRED",
                "variant_a": {"headline": product.get("name"), "price": price},
                "variant_b": {"headline": f"Save time with {product.get('name')}", "price": round(price * 0.95, 2)},
                "success_metric": "verified_paid_orders",
                "auto_publish": False,
            })
        write_json(self.runtime / "ab_tests.json", {"tests": tests, "updated_at": now()})
        return tests

    def portfolio_summary(self):
        products = self.catalog()
        return {
            "businesses_tracked": 1,
            "products": len(products),
            "top_product": max(products, key=lambda p: float(p.get("score", 0) or 0)).get("name") if products else None,
            "average_product_score": round(sum(float(p.get("score", 0) or 0) for p in products) / len(products), 2) if products else 0,
        }

    def run_cycle(self):
        support = self.support_drafts()
        state = {
            "status": "commercial_operations_ready",
            "support_drafts": len(support),
            "funnel": self.funnel(),
            "ab_tests_planned": len(self.ab_tests()),
            "portfolio": self.portfolio_summary(),
            "draft_only_mode": True,
            "external_actions_enabled": False,
            "dashboard_url": "http://127.0.0.1:8776",
            "updated_at": now(),
        }
        write_json(self.live / "commercial_operations_v14_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "commercial_operations_v14_cycle",
            "event_type": "commercial_operations_v14_cycle",
            "state": state,
        })
        return state
