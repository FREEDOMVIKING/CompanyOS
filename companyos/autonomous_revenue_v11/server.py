import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .engine import Engine
E=Engine(Path.home()/"companyos")
class H(BaseHTTPRequestHandler):
 def sendj(self,x,c=200):
  b=json.dumps(x,indent=2,default=str).encode();self.send_response(c);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers()
  try:self.wfile.write(b)
  except BrokenPipeError:pass
 def do_GET(self):
  if self.path.startswith("/api/status"):self.sendj(E.cycle())
  elif self.path.startswith("/api/deliveries"):self.sendj(__import__("json").loads((E.rt/"delivery_index.json").read_text()) if (E.rt/"delivery_index.json").exists() else {"orders":{}})
  else:self.sendj({"error":"not_found"},404)
def main():
 E.cycle();print("CompanyOS Autonomous Revenue V11 started: http://127.0.0.1:8773",flush=True);ThreadingHTTPServer(("127.0.0.1",8773),H).serve_forever()
if __name__=="__main__":main()
