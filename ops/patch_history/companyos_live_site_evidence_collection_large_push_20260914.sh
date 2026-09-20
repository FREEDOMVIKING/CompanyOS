#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a
echo "===== COMPANYOS LIVE SITE EVIDENCE COLLECTION LARGE PUSH ====="
echo "Adds privacy-minimal first-party visit/lead collection. No finance, DNS, or supervisor restart."
mkdir -p companyos/runtime scripts tests/generated

cat > companyos/runtime/site_evidence_collector.py <<'PY'
from __future__ import annotations
import json, secrets, time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from companyos.runtime.market_evidence_engine import MarketEvidenceEngine

class Collector:
    def __init__(self,root):self.root=Path(root);self.engine=MarketEvidenceEngine(root)
    def ingest(self,payload):
        kind=payload.get("kind")
        if kind not in {"page_view","lead","conversion"}:
            return {"accepted":False,"reason":"unsupported_public_event"}
        # Do not store IP, cookies, UA, fingerprint or arbitrary form contents.
        e={"venture_id":str(payload.get("venture_id",""))[:128],"kind":kind,
           "external_id":str(payload.get("event_id") or secrets.token_hex(12))[:128],
           "timestamp":str(payload.get("timestamp") or int(time.time()))[:64]}
        return self.engine.ingest(e)

def handler(root):
    c=Collector(root)
    class H(BaseHTTPRequestHandler):
        def _send(self,code,obj):
            b=json.dumps(obj).encode();self.send_response(code)
            self.send_header("Content-Type","application/json");self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Access-Control-Allow-Headers","Content-Type");self.send_header("Access-Control-Allow-Methods","POST,OPTIONS")
            self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b)
        def do_OPTIONS(self):self._send(204,{})
        def do_GET(self):
            if urlparse(self.path).path=="/health":self._send(200,{"ok":True,"service":"companyos-site-evidence"})
            else:self._send(404,{"ok":False})
        def do_POST(self):
            if urlparse(self.path).path!="/event":return self._send(404,{"ok":False})
            try:
                n=min(int(self.headers.get("Content-Length","0")),8192)
                data=json.loads(self.rfile.read(n) or b"{}")
                r=c.ingest(data);self._send(202 if r.get("accepted") else 400,r)
            except Exception as e:self._send(400,{"accepted":False,"reason":"invalid_request"})
        def log_message(self,*a):pass
    return H
def serve(root,host="127.0.0.1",port=8776):
    ThreadingHTTPServer((host,port),handler(root)).serve_forever()
PY

cat > scripts/companyos_evidence_server <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companyos.runtime.site_evidence_collector import serve
serve(ROOT,os.getenv("COMPANYOS_EVIDENCE_HOST","127.0.0.1"),int(os.getenv("COMPANYOS_EVIDENCE_PORT","8776")))
PY
chmod +x scripts/companyos_evidence_server

cat > companyos/runtime/site_instrumentation.py <<'PY'
from __future__ import annotations
import html,json
from pathlib import Path
def instrument(site_dir,venture_id,endpoint):
    p=Path(site_dir)/"index.html"
    if not p.exists():raise FileNotFoundError(p)
    marker="companyos-evidence-v1"
    s=p.read_text()
    if marker in s:return {"instrumented":False,"reason":"already_instrumented"}
    vid=json.dumps(str(venture_id));ep=json.dumps(str(endpoint).rstrip("/")+"/event")
    js=f"""<script id="{marker}">
(()=>{{const V={vid},E={ep};function send(kind){{const event_id=(crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+Math.random().toString(36).slice(2));fetch(E,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{venture_id:V,kind,event_id,timestamp:new Date().toISOString()}}),keepalive:true}}).catch(()=>{{}})}}send('page_view');document.addEventListener('submit',()=>send('lead'));document.addEventListener('click',e=>{{if(e.target.closest('[data-companyos-conversion]'))send('conversion')}})}})();
</script>"""
    s=s.replace("</body>",js+"</body>") if "</body>" in s else s+js
    p.write_text(s)
    return {"instrumented":True,"venture_id":venture_id,"endpoint":endpoint}
PY

cat > scripts/companyos_instrument_site <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companyos.runtime.site_instrumentation import instrument
p=argparse.ArgumentParser();p.add_argument("--site",required=True);p.add_argument("--venture",required=True);p.add_argument("--endpoint",required=True)
a=p.parse_args();print(json.dumps(instrument(a.site,a.venture,a.endpoint),indent=2))
PY
chmod +x scripts/companyos_instrument_site

cat > tests/generated/test_site_evidence_collection.py <<'PY'
from companyos.runtime.site_evidence_collector import Collector
from companyos.runtime.site_instrumentation import instrument
def test_public_collector_rejects_revenue(tmp_path):
 assert Collector(tmp_path).ingest({"venture_id":"v","kind":"revenue","amount":999})["accepted"] is False
def test_collector_records_attributed_visit(tmp_path):
 c=Collector(tmp_path);assert c.ingest({"venture_id":"v","kind":"page_view","event_id":"pv1","timestamp":"T"})["accepted"]
 assert c.engine.summarize("v")["traffic"]==1
def test_instrumentation(tmp_path):
 d=tmp_path/"site";d.mkdir();(d/"index.html").write_text("<body><form></form></body>")
 r=instrument(d,"venture-1","https://collector.example")
 s=(d/"index.html").read_text()
 assert r["instrumented"] and "companyos-evidence-v1" in s and "venture-1" in s
def test_no_sensitive_browser_collection(tmp_path):
 d=tmp_path/"site";d.mkdir();(d/"index.html").write_text("<body></body>")
 instrument(d,"v","https://x")
 s=(d/"index.html").read_text().lower()
 assert "geolocation" not in s and "fingerprint" not in s and "cookie" not in s
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/site_evidence_collector.py companyos/runtime/site_instrumentation.py scripts/companyos_evidence_server scripts/companyos_instrument_site
python -m pytest -q tests/generated/test_market_evidence_engine.py tests/generated/test_site_evidence_collection.py

echo "===== LOCAL COLLECTOR COMMISSIONING ====="
python scripts/companyos_evidence_server > .companyos_runtime/evidence_server_test.log 2>&1 &
EPID=$!
trap 'kill "$EPID" 2>/dev/null || true' EXIT
sleep 1
curl -fsS http://127.0.0.1:8776/health
echo
TESTVID="collector-commissioning-$(date +%s)"
curl -fsS -X POST http://127.0.0.1:8776/event -H 'Content-Type: application/json' \
 --data "{\"venture_id\":\"$TESTVID\",\"kind\":\"page_view\",\"event_id\":\"pv-1\",\"timestamp\":\"commissioning\"}"
echo
python scripts/companyos_evidencectl summary --venture "$TESTVID"
kill "$EPID" 2>/dev/null || true
trap - EXIT

echo "===== COMMIT ONLY THIS PUSH ====="
git add companyos/runtime/site_evidence_collector.py companyos/runtime/site_instrumentation.py scripts/companyos_evidence_server scripts/companyos_instrument_site tests/generated/test_site_evidence_collection.py
git commit -m "add first party live site evidence collection" || true
echo "===== FINAL ====="
git rev-parse --short HEAD
git status --short
echo "COMPANYOS_LIVE_SITE_EVIDENCE_COLLECTION=PASS"
