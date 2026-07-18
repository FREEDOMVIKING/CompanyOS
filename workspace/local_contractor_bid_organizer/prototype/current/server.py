from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
root=Path(__file__).resolve().parent/"frontend"
os.chdir(root)
server=ThreadingHTTPServer(("127.0.0.1",8765),SimpleHTTPRequestHandler)
print("Open http://127.0.0.1:8765")
print("Press Ctrl+C to stop.")
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
