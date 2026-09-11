#!/usr/bin/env python3
import json
from companyos_phase93_100 import (
    MissionBoard, AutonomousQueue, ArtifactRegistry, ApprovalCenter,
    ProductionReadiness, ExternalActionRouter, AuditTrail, ProductionCEO
)

m = MissionBoard().transition({"id":"m1","status":"queued"}, "active")
assert m["transition_ok"] is True

q = AutonomousQueue().select([
    {"id":"a","status":"queued","priority":10,"value":5,"risk":1},
    {"id":"b","status":"queued","priority":99,"requires_external_action":True},
])
assert [x["id"] for x in q] == ["a"]

art = ArtifactRegistry().register("report","Test artifact","a")
assert art["artifact_id"].startswith("art-")

ap = ApprovalCenter()
assert len(ap.pending([{"id":"x","approval_required":True,"approved":False}])) == 1

ready = ProductionReadiness().evaluate({
    "tests":1,"monitoring":1,"rollback":1,"security":1,"observability":1
})
assert ready["ready"] is True

route = ExternalActionRouter().route({"type":"send_payment","external":True})
assert route["approval_required"] is True
assert route["dispatch_allowed"] is False
assert route["dispatched"] is False

audit = AuditTrail()
assert audit.record("test",{"ok":True})["event_id"].startswith("evt-")

cycle = ProductionCEO().run({
    "tasks":[
        {"id":"t1","title":"Internal research","status":"queued","priority":10,"value":5,"risk":1},
        {"id":"t2","title":"External publish","status":"queued","priority":20,"value":5,"risk":1,"requires_external_action":True}
    ],
    "actions":[
        {"id":"a1","type":"publish_public","external":True,"approval_required":True,"approved":False}
    ],
    "readiness":{"tests":1,"monitoring":1,"rollback":1,"security":1,"observability":1}
})
assert cycle["success"] is True
assert cycle["status"] == "phase100_production_ceo_cycle_completed"
assert cycle["external_action_taken"] is False
assert cycle["irreversible_action_taken"] is False

print(json.dumps({
    "success": True,
    "status": "phase93_100_verification_passed",
    "cycle_status": cycle["status"],
    "selected_tasks": len(cycle["selected_tasks"]),
    "pending_approvals": len(cycle["pending_approvals"]),
    "external_action_taken": cycle["external_action_taken"],
    "irreversible_action_taken": cycle["irreversible_action_taken"],
}, indent=2))
