import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import VenturePromotionPipelineV39

HOST, PORT = "127.0.0.1", 8801
ENGINE = VenturePromotionPipelineV39(Path.home() / "companyos")

def esc(s):
    s = "" if s is None else str(s)
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&#39;"))

def page():
    s = ENGINE.run_cycle()
    cards = "".join(
        f"""<article>
        <h2>{esc(v.get('venture_name'))}</h2>
        <p>Venture ID: {esc(v.get('venture_id'))}</p>
        <p>Review ID: {esc(v.get('review_id'))}</p>
        <p>Launch score: {esc(v.get('launch_score'))}</p>
        <p>Status: {esc(v.get('status'))}</p>
        </article>"""
        for v in s.get("promotions", [])
    )

    failures = "".join(
        f"""<article>
        <h2>{esc(v.get('venture_name'))}</h2>
        <p>Status: {esc(v.get('status'))}</p>
        <p>Problems: {esc(', '.join(v.get('problems', [])))}</p>
        </article>"""
        for v in s.get("failures", [])
    )

    return f"""<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Venture Promotion Pipeline</title>
<style>
body{{font-family:system-ui;background:#08101f;color:#eef2ff;margin:0}}
main{{max-width:1100px;margin:auto;padding:30px 20px}}
.hero,article{{background:#151d33;padding:22px;border-radius:18px;margin-bottom:18px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.big{{font-size:36px;font-weight:800}}
</style></head><body><main>
<h1>CompanyOS Venture Promotion Pipeline</h1>
<section class="hero">
<p>Status: {esc(s.get('status'))}</p>
<p class="big">Promoted: {s.get('promoted')}</p>
<p>Source approvals: {s.get('source_approvals')}</p>
<p>Failed promotions: {s.get('failed')}</p>
<p>Pending: {s.get('pending')}</p>
<p>Automatic external execution: {s.get('automatic_external_execution_enabled')}</p>
</section>
<h2>Promoted to V38 Intake</h2>
<section class="grid">{cards or '<article><p>No approved ventures available yet.</p></article>'}</section>
<h2>Promotion Failures</h2>
<section class="grid">{failures or '<article><p>No promotion failures.</p></article>'}</section>
</main></body></html>"""

class H(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        b=json.dumps(obj,indent=2,default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers()
        try: self.wfile.write(b)
        except BrokenPipeError: pass

    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/status":
            return self.send_json(ENGINE.run_cycle())
        if p=="/api/promotions":
            return self.send_json({"promotions":ENGINE.run_cycle().get("promotions",[])})
        if p=="/api/failures":
            return self.send_json({"failures":ENGINE.run_cycle().get("failures",[])})
        if p in ("/","/index.html"):
            b=page().encode()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        return self.send_json({"error":"not_found"},404)

def main():
    ENGINE.run_cycle()
    print("CompanyOS Venture Promotion Pipeline V39 started: http://127.0.0.1:8801", flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()

if __name__=="__main__":
    main()
