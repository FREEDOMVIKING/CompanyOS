from companyos_phase609_624 import BuildAcceptance, QAGate, DeliveryRuntime

def test_build_acceptance():
    result = BuildAcceptance().evaluate({
        "artifacts":["a"],"core_workflow_verified":True,
        "tests_passed":True,"documentation_present":True
    })
    assert result["accepted"] is True

def test_qa_gate():
    evidence = {
        "targeted_tests_pass":True,"regression_tests_pass":True,
        "no_known_critical_defects":True,"core_workflow_verified":True,
        "telemetry_verified":True
    }
    assert QAGate().evaluate(evidence)["passed"] is True

def test_runtime():
    assert DeliveryRuntime().status()["status"] == "phase624_autonomous_product_delivery_ready"
