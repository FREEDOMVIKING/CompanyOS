#!/usr/bin/env python3
import json
import os
import tempfile
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

from companyos.specialistops import SpecialistCapabilityRouter, SpecialistOpsStatus

class MockReasoner(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.dumps({
            "success": True,
            "mode": "external_provider",
            "provider_response": {
                "model": "mock-specialist-model",
                "choices": [{"message": {"content": "{\"result\":\"ok\"}"}}]
            }
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        return

server = HTTPServer(("127.0.0.1", 0), MockReasoner)
threading.Thread(target=server.serve_forever, daemon=True).start()
os.environ["COMPANYOS_REASONING_URL"] = f"http://127.0.0.1:{server.server_port}/reason"

root = Path(tempfile.mkdtemp())
router = SpecialistCapabilityRouter(root)
results = {}
for dept in ["research","finance","product","growth","operations","customer_success"]:
    r = router.execute(
        {"job_id": f"verify_{dept}", "kind":"analysis", "payload":{"instruction":f"Verify {dept}", "success_criteria":["success"]}},
        dept
    )
    assert r["success"] is True, (dept, r)
    results[dept] = True

server.shutdown()

print(json.dumps({
    "success": True,
    "status": "phase17001_17500_verification_passed",
    "cycle_status": "phase17500_specialist_capability_expansion_ready",
    "departments_verified": results
}, indent=2))
