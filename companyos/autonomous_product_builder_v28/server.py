
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import AutonomousProductBuilderV28

HOST, PORT = "127.0.0.1", 8790
ENGINE = AutonomousProductBuilderV28(Path.home() / "companyos")

def page():
    state = ENGINE.run_cycle()
    cards = "".join(
        f"""<article>
        <h2>{x.get('name')}</h2>
        <p>Type: {x.get('product_type')}</p>
        <p>Version: {x.get('version')}</p>
        <p>Quality score: {x.get('quality_score')} / 100</p>
        <p>State: {x.get('state')}</p>
        <p>Recommended price: ${x.get('pricing',{}).get('recommended')}</p>
        <p class="path">{x.get('workspace')}</p>
        </article>"""
        for x in state.get("products", [])
    )
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Autonomous Product Builder</title>
    <style>
    body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
    main{{max-width:1100px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}}
    .path{{word-break:break-all;color:#b9ccff}}
    </style></head><body><main>
    <h1>CompanyOS Autonomous Product Builder</h1>
    <section class="hero">
      <p>Status: {state.get('status')}</p>
      <p>Products built: {state.get('products_built')}</p>
      <p>Ready for review: {state.get('products_ready_for_review')}</p>
      <p>Automatic external publishing: {state.get('automatic_external_publish_enabled')}</p>
      <p>Automatic customer delivery: {state.get('automatic_customer_delivery_enabled')}</p>
    </section>
    <h2>Product Portfolio</h2>
    <section class="grid">{cards or '<article><p>No approved opportunities available.</p></article>'}</section>
    </main></body></html>"""

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
        path = urlparse(self.path).path
        if path == "/api/status":
            self.send_json(ENGINE.run_cycle())
            return
        if path == "/api/products":
            self.send_json({"products": ENGINE.run_cycle().get("products", [])})
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
    print(f"CompanyOS Autonomous Product Builder V28 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
