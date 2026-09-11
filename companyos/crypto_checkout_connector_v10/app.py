import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8772
STOREFRONT_API = "http://127.0.0.1:8770"
PAYMENT_API = "http://127.0.0.1:8771"

def get_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def post_json(url, payload, timeout=10):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        try:
            data = json.loads(raw)
        except Exception:
            data = {"ok": False, "error": raw or str(exc)}
        return exc.code, data

def catalog():
    return get_json(STOREFRONT_API + "/api/catalog")

def payment_status():
    return get_json(PAYMENT_API + "/api/status")

def invoices():
    return get_json(PAYMENT_API + "/api/invoices")

def render_page():
    cat = catalog()
    pay = payment_status()
    wallet_ready = bool(pay.get("wallet_public_address_loaded"))
    wallet_masked = pay.get("wallet_public_address_masked") or "not loaded"

    cards = []
    for item in cat.get("products", []):
        product_id = item.get("product_id", "")
        name = item.get("name", product_id)
        price = item.get("pricing", {}).get("recommended", 0)
        quality = item.get("quality_passed", False)
        disabled = "" if wallet_ready and quality else "disabled"
        cards.append(f"""
        <article class="card">
          <h2>{name}</h2>
          <p>Quality passed: {str(bool(quality)).lower()}</p>
          <p class="price">${price}</p>
          <button {disabled} onclick="openCheckout('{product_id}','{name}',{price})">
            Pay with crypto
          </button>
        </article>
        """)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Crypto Storefront</title>
<style>
body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
main{{max-width:1000px;margin:auto;padding:38px 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}}
.card,.panel{{background:#151d33;padding:22px;border-radius:18px}}
.price{{font-size:1.8rem;font-weight:800}}
button{{padding:12px 16px;border:0;border-radius:10px;font-weight:800}}
button:disabled{{opacity:.45}}
.notice{{background:#26304a;padding:14px;border-radius:12px;margin-bottom:20px}}
#modal{{display:none;position:fixed;inset:0;background:#000b;padding:18px;overflow:auto}}
#modalBox{{max-width:680px;margin:30px auto;background:#151d33;padding:24px;border-radius:18px}}
input{{width:100%;box-sizing:border-box;padding:12px;border-radius:10px;border:1px solid #46506a;background:#0b1020;color:#fff}}
pre{{white-space:pre-wrap;word-break:break-word;background:#090d18;padding:14px;border-radius:12px}}
.close{{float:right}}
</style>
</head>
<body>
<main>
<h1>CompanyOS Crypto Storefront</h1>
<div class="notice">
Crypto bridge: {'ready' if wallet_ready else 'wallet setup required'} · Receiving wallet: {wallet_masked}
</div>
<div class="grid">{''.join(cards)}</div>
</main>

<div id="modal">
  <div id="modalBox">
    <button class="close" onclick="closeCheckout()">Close</button>
    <h2 id="productName">Crypto checkout</h2>
    <p id="productPrice"></p>
    <label>Delivery email</label>
    <input id="email" type="email" placeholder="customer@example.com">
    <p><button onclick="createInvoice()">Create payment invoice</button></p>
    <div id="result"></div>
  </div>
</div>

<script>
let selectedProduct = null;
let currentInvoice = null;

function openCheckout(id,name,price){{
  selectedProduct = id;
  currentInvoice = null;
  document.getElementById('productName').textContent = name;
  document.getElementById('productPrice').textContent = '$' + price;
  document.getElementById('result').innerHTML = '';
  document.getElementById('modal').style.display = 'block';
}}

function closeCheckout(){{
  document.getElementById('modal').style.display = 'none';
}}

async function createInvoice(){{
  const email = document.getElementById('email').value.trim();
  if(!email || !email.includes('@')) {{
    alert('Enter a valid delivery email.');
    return;
  }}
  const response = await fetch('/api/checkout', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{product_id:selectedProduct,email}})
  }});
  const data = await response.json();
  if(!response.ok) {{
    document.getElementById('result').innerHTML = '<pre>'+JSON.stringify(data,null,2)+'</pre>';
    return;
  }}
  currentInvoice = data.invoice.invoice_id;
  const inv = data.invoice;
  document.getElementById('result').innerHTML = `
    <div class="panel">
      <h3>Payment invoice created</h3>
      <p><strong>Status:</strong> ${{inv.status}}</p>
      <p><strong>Chain:</strong> ${{inv.chain}}</p>
      <p><strong>Amount:</strong> ${{inv.amount_usd}} USD equivalent</p>
      <p><strong>Send to:</strong></p>
      <pre>${{inv.wallet_address}}</pre>
      <p><strong>Memo/reference:</strong></p>
      <pre>${{inv.memo}}</pre>
      <p>Send the configured SOL or USDC amount to the address above. CompanyOS will verify the blockchain payment before fulfillment.</p>
      <button onclick="checkInvoice()">Check payment status</button>
    </div>`;
}}

async function checkInvoice(){{
  if(!currentInvoice) return;
  const response = await fetch('/api/invoice-status?id='+encodeURIComponent(currentInvoice));
  const data = await response.json();
  document.getElementById('result').innerHTML += '<pre>'+JSON.stringify(data,null,2)+'</pre>';
}}
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        body = json.dumps(obj, indent=2, default=str).encode("utf-8")
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
        if path in ("/", "/index.html"):
            try:
                body = render_page().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 503)
            return

        if path == "/api/status":
            try:
                self.send_json({
                    "status": "crypto_checkout_connector_ready",
                    "storefront": get_json(STOREFRONT_API + "/api/status"),
                    "payment_bridge": payment_status(),
                    "checkout_url": f"http://{HOST}:{PORT}",
                })
            except Exception as exc:
                self.send_json({"status": "dependency_unavailable", "error": str(exc)}, 503)
            return

        if path == "/api/invoice-status":
            query = urlparse(self.path).query
            invoice_id = ""
            for pair in query.split("&"):
                if pair.startswith("id="):
                    invoice_id = pair[3:]
            try:
                get_json(PAYMENT_API + "/api/check")
                data = invoices()
                invoice = next(
                    (x for x in data.get("invoices", []) if x.get("invoice_id") == invoice_id),
                    None,
                )
                if not invoice:
                    self.send_json({"ok": False, "error": "invoice_not_found"}, 404)
                else:
                    self.send_json({"ok": True, "invoice": invoice})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 503)
            return

        self.send_json({"ok": False, "error": "not_found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/checkout":
            self.send_json({"ok": False, "error": "not_found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            product_id = payload.get("product_id")
            email = str(payload.get("email") or "").strip()
            if not product_id:
                self.send_json({"ok": False, "error": "product_id_required"}, 400)
                return
            if "@" not in email:
                self.send_json({"ok": False, "error": "valid_email_required"}, 400)
                return
            code, data = post_json(
                PAYMENT_API + "/api/invoices",
                {"product_id": product_id, "email": email},
            )
            self.send_json(data, code)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 503)

def main():
    print(f"CompanyOS Crypto Checkout Connector V10 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
