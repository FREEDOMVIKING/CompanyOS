import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .bridge import CryptoPaymentBridgeV9

HOST = "127.0.0.1"
PORT = 8771
ENGINE = CryptoPaymentBridgeV9(Path.home() / "companyos")

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
        if path == "/api/invoices":
            self.send_json(ENGINE.invoices())
            return
        if path == "/api/check":
            self.send_json(ENGINE.check_invoices())
            return
        self.send_json({"ok": False, "error": "not_found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/invoices":
            self.send_json({"ok": False, "error": "not_found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            result, code = ENGINE.create_invoice(
                payload.get("product_id"),
                payload.get("email"),
            )
            self.send_json(result, code)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)

def main():
    ENGINE.status()
    print(f"CompanyOS Crypto Payment Bridge V9 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
