import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from companyos.governance.venture_identity_progression import evaluate_all
HOST,PORT='127.0.0.1',8770
HTML=Path(__file__).with_name('venture_identity_progression.html')
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/progression'):
            b=json.dumps({'ventures':evaluate_all()},indent=2,default=str).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        b=HTML.read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def log_message(self,*a): pass
if __name__=='__main__':
    print(f'Venture Identity + Progression: http://{HOST}:{PORT}',flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
