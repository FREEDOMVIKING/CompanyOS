#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase609_624 import (
    DeliveryIntake,ProductSpec,ImplementationPlan,SpecialistPlan,ArtifactManifest,
    BuildAcceptance,QAGate,ReleaseCandidate,DeploymentReadiness,LaunchPlan,
    TelemetryContract,OutcomeCapture,DeliveryFeedback,ProductDeliveryManager,
    CEODeliveryBridge,DeliveryRuntime
)

packet = {
    "success":True,
    "venture_id":"v1",
    "brief":{"product_name":"X","target_customer":"businesses","problem":"slow workflow"},
    "mvp_scope":{"must_have":["core"],"defer":["extra"]},
    "quality_gates":["targeted_tests_pass"],
    "kpis":{"activation":["activation_rate"]},
}

assert DeliveryIntake().evaluate(packet)["accepted"] is True
spec = ProductSpec().build(packet)
assert spec["stage"] == "mvp_delivery"
tasks = ImplementationPlan().build(spec)
assert len(tasks) >= 5
assert SpecialistPlan().assign(tasks)[0]["assigned_role"]
root = Path(tempfile.mkdtemp(prefix="phase624_"))
assert ArtifactManifest(root).append("v1",["a"])["venture_id"] == "v1"

build = {
    "artifacts":["a"],
    "core_workflow_verified":True,
    "tests_passed":True,
    "documentation_present":True,
}
assert BuildAcceptance().evaluate(build)["accepted"] is True

qa_evidence = {
    "targeted_tests_pass":True,
    "regression_tests_pass":True,
    "no_known_critical_defects":True,
    "core_workflow_verified":True,
    "telemetry_verified":True,
    "rollback_ready":True,
    "telemetry_ready":True,
    "secrets_configured_safely":True,
    "support_path_ready":True,
}
qa = QAGate().evaluate(qa_evidence)
assert qa["passed"] is True
rc = ReleaseCandidate().create("v1", qa, ["a"])
assert rc["release_candidate_ready"] is True
assert rc["external_launch_authorized"] is False
assert DeploymentReadiness().evaluate({**qa_evidence,"release_candidate_ready":True})["ready"] is True
assert LaunchPlan().build()["automatic_irreversible_launch"] is False
assert TelemetryContract().build(packet["kpis"])["required_events"]
out = OutcomeCapture().capture({"deployment_success":True,"activation_rate":0.3})
fb = DeliveryFeedback().build(out)
assert fb["mission_success"] is True
assert ProductDeliveryManager().prepare(packet)["success"] is True
assert CEODeliveryBridge().prepare(packet)["success"] is True
assert DeliveryRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase609_624_verification_passed",
    "cycle_status":"phase624_autonomous_product_delivery_ready",
    "product_specification":True,
    "implementation_planning":True,
    "specialist_delivery_plan":True,
    "artifact_manifest":True,
    "build_acceptance":True,
    "qa_gate":True,
    "release_candidate_promotion":True,
    "deployment_readiness":True,
    "controlled_launch_plan":True,
    "telemetry_contract":True,
    "outcome_capture":True,
    "feedback_to_lifecycle":True,
    "autonomy_mode":"high"
}, indent=2))
