import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from .engine import AutonomousLaunchControlV37

HOST, PORT = "127.0.0.1", 8799
ENGINE = AutonomousLaunchControlV37(Path.home() / "companyos")

def esc(s):
    s = "" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def page(message=""):
    s = ENGINE.run_cycle()
    cards = []
    for r in s.get("reviews", []):
        decision = r.get("executive_decision") or "PENDING"
        buttons = ""
        if not r.get("executive_decision"):
            rid = esc(r.get("review_id"))
            buttons = f"""
            <form method="POST" action="/decision">
              <input type="hidden" name="review_id" value="{rid}">
              <input name="reason" placeholder="Optional reason">
              <button name="decision" value="APPROVE">Approve for launch prep</button>
              <button name="decision" value="HOLD">Hold</button>
              <button name="decision" value="REJECT">Reject</button>
            </form>"""
        cards.append(f"""<article>
          <h2>{esc(r.get('venture_name'))}</h2>
          <p>Launch score: {esc(r.get('launch_score'))}</p>
          <p>Launch state: {esc(r.get('launch_state'))}</p>
          <p>Executive decision: {esc(decision)}</p>
          <p>Effective status: {esc(r.get('effective_status'))}</p>
          <p>Blockers: {esc(', '.join(r.get('blockers',[])) or 'None')}</p>
          {buttons}
        </article>""")

    a = s.get("analytics", {})
    msg = f'<div class="msg">{esc(message)}</div>' if message else ""
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CompanyOS Executive Approval</title>
    <style>
    body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
    main{{max-width:1100px;margin:auto;padding:30px 20px}}
    .hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
    button,input{{font:inherit;padding:10px 12px;margin:6px 4px 0 0;border-radius:10px;border:0}}
    button{{cursor:pointer}} .msg{{padding:12px;background:#263454;border-radius:12px;margin-bottom:16px}}
    .big{{font-size:36px;font-weight:800}}
    </style></head><body><main>
    <h1>CompanyOS Autonomous Executive Approval & Launch Control</h1>
    {msg}
    <section class="hero">
      <p>Status: {esc(s.get('status'))}</p>
      <p class="big">Pending approvals: {a.get('pending',0)}</p>
      <p>Approved: {a.get('approved',0)}</p>
      <p>Held: {a.get('held',0)}</p>
      <p>Rejected: {a.get('rejected',0)}</p>
      <p>Average launch score: {a.get('average_launch_score',0)}</p>
      <p>Automatic external launch: {s.get('automatic_external_launch_enabled')}</p>
      <p>Automatic publication: {s.get('automatic_publication_enabled')}</p>
    </section>
    <h2>Executive Review Queue</h2>
    <section class="grid">{''.join(cards) or '<article><p>No launch reviews are currently queued.</p></article>'}</section>
    </main></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, body, code=200, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(json.dumps(obj, indent=2, default=str), code, "application/json")

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/api/status":
            return self._json(ENGINE.run_cycle())
        if p == "/api/reviews":
            return self._json({"reviews": ENGINE.run_cycle().get("reviews", [])})
        if p == "/api/approved":
            return self._json({"approved": ENGINE.run_cycle().get("approved_for_launch_prep", [])})
        if p in ("/", "/index.html"):
            return self._send(page())
        return self._json({"error":"not_found"}, 404)

    def do_POST(self):
        p = urlparse(self.path).path
        if p != "/decision":
            return self._json({"error":"not_found"}, 404)

        length = int(self.headers.get("Content-Length","0"))
        data = parse_qs(self.rfile.read(length).decode())
        review_id = (data.get("review_id") or [""])[0]
        decision = (data.get("decision") or [""])[0]
        reason = (data.get("reason") or [""])[0]

        try:
            record = ENGINE.make_decision(review_id, decision, reason=reason)
            return self._send(page(f"{record['decision']} recorded for {record['venture_name']}."))
        except Exception as e:
            return self._send(page(f"Decision failed: {e}"), 400)

def main():
    ENGINE.run_cycle()
    print("CompanyOS Autonomous Launch Control V37 started: http://127.0.0.1:8799", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
