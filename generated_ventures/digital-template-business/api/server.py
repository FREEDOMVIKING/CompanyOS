from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/health':
            body=json.dumps({'ok':True}).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        else: self.send_response(404); self.end_headers()
if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',8891),H).serve_forever()
