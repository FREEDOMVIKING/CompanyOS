import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import AutonomousExecutionEngineV38

HOST, PORT = "127.0.0.1", 8800
ENGINE = AutonomousExecutionEngineV38(Path.home() / "companyos")

def esc(s):
    s = "" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def page():
    s = ENGINE.run_cycle()
    cards = []
    for x in s.get("executions", []):
        cards.append(f"""<article>
        <h2>{esc(x.get('venture_name'))}</h2>
        <p>Execution ID: {esc(x.get('execution_id'))}</p>
        <p>Status: {esc(x.get('status'))}</p>
        <p>Completed steps: {len(x.get('completed_steps', []))}</p>
        <p>Failed steps: {len(x.get('failed_steps', []))}</p>
        <p>Workspace: {esc(x.get('artifacts',{}).get('workspace'))}</p>
        <p>External execution: {x.get('automatic_external_execution_enabled')}</p>
        </article>""")

    return f"""<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Autonomous Execution Engine</title>
<style>
body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
main{{max-width:1100px;margin:auto;padding:30px 20px}}
.hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.big{{font-size:36px;font-weight:800}}
</style></head><body><main>
<h1>CompanyOS Autonomous Execution Engine</h1>
<section class="hero">
<p>Status: {esc(s.get('status'))}</p>
<p class="big">Executions: {s.get('executions_total')}</p>
<p>Approved ventures received: {s.get('approved_ventures_received')}</p>
<p>Ready for external execution review: {s.get('ready_for_external_execution_review')}</p>
<p>Failed executions: {s.get('failed_executions')}</p>
<p>Automatic external execution: {s.get('automatic_external_execution_enabled')}</p>
<p>Automatic publication: {s.get('automatic_publication_enabled')}</p>
<p>Automatic spending: {s.get('automatic_spending_enabled')}</p>
</section>
<h2>Execution Queue</h2>
<section class="grid">{''.join(cards) or '<article><p>No approved ventures have been received from V37 yet.</p></article>'}</section>
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
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _json(self, obj, code=200):
        self._send(json.dumps(obj, indent=2, default=str), code, "application/json")

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/api/status":
            return self._json(ENGINE.run_cycle())
        if p == "/api/executions":
            return self._json({"executions": ENGINE.run_cycle().get("executions", [])})
        if p == "/api/review-queue":
            q = json.loads((ENGINE.live / "external_execution_review_queue_v38.json").read_text()) if (ENGINE.live / "external_execution_review_queue_v38.json").exists() else {"executions":[]}
            return self._json(q)
        if p in ("/", "/index.html"):
            return self._send(page())
        return self._json({"error":"not_found"}, 404)

def main():
    ENGINE.run_cycle()
    print("CompanyOS Autonomous Execution Engine V38 started: http://127.0.0.1:8800", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
