import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .engine import StorefrontSalesEngineV8

HOST = "127.0.0.1"
PORT = 8770
HOME = Path.home() / "companyos"
ENGINE = StorefrontSalesEngineV8(HOME)

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        body = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/catalog":
            self.send_json(ENGINE.build_catalog())
            return
        if path == "/api/status":
            self.send_json(ENGINE.run())
            return
        if path == "/api/orders":
            self.send_json(ENGINE.order_ledger())
            return
        if path in ("/", "/index.html"):
            ENGINE.run()
            body = (ENGINE.storefront / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"ok": False, "error": "not_found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/orders":
            self.send_json({"ok": False, "error": "not_found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            result, code = ENGINE.create_order(
                payload.get("product_id"),
                payload.get("email"),
            )
            self.send_json(result, code)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)

def main():
    ENGINE.run()
    print(f"CompanyOS Storefront Sales V8 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
