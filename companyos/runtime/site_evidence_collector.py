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
