from companyos_phase401_416 import VentureIntake, VentureOrchestrator, VentureRuntime

def thesis():
    return {"name":"X","customer":"businesses","core_problem":"slow work","business_model":{"primary":"SaaS"}}

def test_validation_gate():
    assert VentureIntake().accept({"decision":{"decision":"go_to_mvp"}})["accepted"] is True

def test_factory_packet():
    result = VentureOrchestrator().prepare(thesis(), {"decision":{"decision":"go_to_mvp"}})
    assert result["success"] is True
    assert result["task_graph"]
    assert result["quality_gates"]

def test_runtime():
    assert VentureRuntime().status()["status"] == "phase416_venture_factory_ready"
