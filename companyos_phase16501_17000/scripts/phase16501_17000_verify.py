#!/usr/bin/env python3
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from companyos.ceointelligence import AutonomousCEOOrchestrator, CEOIntelligenceStatus
from companyos.daemonops import DurableJobQueue

class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        plan = {
            "objective": "verification",
            "assumptions": ["mock reasoning"],
            "tasks": [
                {
                    "id":"task_1",
                    "department":"research",
                    "kind":"research",
                    "instruction":"Verify integration",
                    "priority":8,
                    "requires_approval":False,
                    "success_criteria":["integration verified"]
                },
                {
                    "id":"task_2",
                    "department":"operations",
                    "kind":"production_deploy",
                    "instruction":"Do not actually deploy",
                    "priority":5,
                    "requires_approval":True,
                    "success_criteria":["approval required"]
                }
            ],
            "stop_conditions":["verification complete"]
        }
        provider = {
            "model":"mock-model",
            "choices":[{"message":{"content":json.dumps(plan)}}]
        }
        body=json.dumps({
            "success":True,
            "mode":"external_provider",
            "provider_response":provider
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        return

server=HTTPServer(("127.0.0.1",0),MockHandler)
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()

root=Path(tempfile.mkdtemp())
queue=DurableJobQueue(root)
url=f"http://127.0.0.1:{server.server_port}/reason"
ceo=AutonomousCEOOrchestrator(root,reasoning_url=url)
result=ceo.plan_and_delegate("verification objective",queue)

assert result["success"] is True
assert result["delegation"]["delegated_count"] == 1
assert result["delegation"]["approval_count"] == 1
assert queue.next_job() is not None
assert CEOIntelligenceStatus().status()["status"] == "phase17000_autonomous_ceo_intelligence_integration_ready"

server.shutdown()

print(json.dumps({
    "success":True,
    "status":"phase16501_17000_verification_passed",
    "cycle_status":"phase17000_autonomous_ceo_intelligence_integration_ready",
    "live_api_test_required_separately":True
},indent=2))
