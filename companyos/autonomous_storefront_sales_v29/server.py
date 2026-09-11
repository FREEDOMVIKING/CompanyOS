
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .engine import AutonomousStorefrontSalesV29

HOST, PORT = "127.0.0.1", 8791
ENGINE = AutonomousStorefrontSalesV29(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    cards = "".join(
        f"""<article>
        <h2>{x.get('name')}</h2>
        <p>Type: {x.get('product_type')}</p>
        <p>Version: {x.get('version')}</p>
        <p>Quality: {x.get('quality_score')} / 100</p>
        <p>Price: ${x.get('price_usd')}</p>
        <p>State: {x.get('state')}</p>
        <a href="/checkout?product_id={x.get('product_id')}">Local checkout</a>
        </article>"""
        for x in state.get("catalog", [])
    )
    a = state.get("analytics", {})
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Autonomous Storefront & Sales</title>
    <style>
    body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
    main{{max-width:1100px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
    a{{display:inline-block;background:#eef2ff;color:#08101f;padding:12px 16px;border-radius:12px;text-decoration:none;font-weight:700}}
    </style></head><body><main>
    <h1>CompanyOS Autonomous Storefront & Sales</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Products: {a.get('products_total')}</p>
      <p>Orders: {a.get('orders_total')}</p>
      <p>Paid orders: {a.get('orders_paid')}</p>
      <p>Verified revenue: ${a.get('verified_revenue_usd')}</p>
      <p>Public storefront enabled: {state.get('public_storefront_enabled')}</p>
      <p>Local checkout enabled: {state.get('local_checkout_enabled')}</p>
    </section>
    <h2>Product Catalog</h2>
    <section class="grid">{cards or '<article><p>No V28 products found.</p></article>'}</section>
    </main></body></html>"""

def checkout_page(product_id):
    catalog = {x["product_id"]: x for x in ENGINE.catalog()}
    p = catalog.get(product_id)
    if not p:
        return "<h1>Product not found</h1>"
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{{font-family:system-ui;background:#08101f;color:#eef2ff;padding:30px}}section{{max-width:700px;background:#151d33;padding:24px;border-radius:18px}}</style>
    </head><body><section><h1>{p['name']}</h1><p>Version {p['version']}</p><p>Price: ${p['price_usd']}</p>
    <p>This local checkout creates a pending order and routes payment verification through the existing crypto bridge.</p>
    <p>Use API: <code>/api/create-order?product_id={p['product_id']}</code></p></section></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        body = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        q = parse_qs(parsed.query)

        if path == "/api/status":
            self.send_json(ENGINE.run_cycle())
            return
        if path == "/api/catalog":
            self.send_json({"catalog": ENGINE.catalog()})
            return
        if path == "/api/orders":
            self.send_json({"orders": ENGINE.load_orders()})
            return
        if path == "/api/create-order":
            product_id = q.get("product_id", [None])[0]
            try:
                self.send_json(ENGINE.create_order(product_id))
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
            return
        if path == "/checkout":
            body = checkout_page(q.get("product_id", [""])[0]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path in ("/", "/index.html"):
            body = page().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"error": "not_found"}, 404)

def main():
    ENGINE.run_cycle()
    print(f"CompanyOS Autonomous Storefront & Sales V29 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
