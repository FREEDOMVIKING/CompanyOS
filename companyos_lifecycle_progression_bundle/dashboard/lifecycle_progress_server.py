import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from companyos.governance.venture_lifecycle_progression import evaluate_known,STATE
HOST,PORT="127.0.0.1",8769
HTML=Path(__file__).with_name("lifecycle_progress.html")
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path.startswith("/api/lifecycle"):
   data={"ventures":evaluate_known()}
   b=json.dumps(data,indent=2).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b);return
  b=HTML.read_bytes();self.send_response(200);self.send_header("Content-Type","text/html");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def log_message(self,*a):pass
if __name__=="__main__":
 print(f"Lifecycle Progression: http://{HOST}:{PORT}",flush=True);ThreadingHTTPServer((HOST,PORT),H).serve_forever()
