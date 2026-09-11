from companyos_phase721_736 import TestMissionFactory, StressPlan, HarnessRuntime

def test_mission_factory():
    m=TestMissionFactory().create()
    assert m["context"]["integration_test"] is True

def test_stress_plan_bounded():
    assert StressPlan().build(100)["rounds"]==10

def test_runtime():
    assert HarnessRuntime().status()["status"]=="phase736_end_to_end_mission_integration_harness_ready"
