#!/usr/bin/env python3
import json, tempfile, threading, os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

from companyos.failureops import FailureClassifier, GenericSpecialist, RecoveryRouter, VerificationPolicy, FailureOpsStatus

class Mock(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.dumps({
            "success": True,
            "mode": "external_provider",
            "provider_response": {
                "model": "mock-recovery-model",
                "choices": [{"message":{"content":"recovered"}}]
            }
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*args):
        return

server=HTTPServer(("127.0.0.1",0),Mock)
threading.Thread(target=server.serve_forever,daemon=True).start()
os.environ["COMPANYOS_REASONING_URL"]=f"http://127.0.0.1:{server.server_port}/reason"

root=Path(tempfile.mkdtemp())
job={"job_id":"x","kind":"market_scan","payload":{"instruction":"recover unsupported internal work"}}
failed={"success":False,"error":"unsupported_specialist_department"}

assert FailureClassifier().classify(job,failed)["recoverable"] is True
rec=RecoveryRouter(root).recover(job,"research",failed)
assert rec["recovered"] is True
assert VerificationPolicy().verify(job,rec["result"])["passed"] is True
assert FailureOpsStatus().status()["status"]=="phase18000_failure_closure_and_verification_ready"

server.shutdown()

print(json.dumps({
    "success":True,
    "status":"phase17501_18000_verification_passed",
    "cycle_status":"phase18000_failure_closure_and_verification_ready"
},indent=2))
