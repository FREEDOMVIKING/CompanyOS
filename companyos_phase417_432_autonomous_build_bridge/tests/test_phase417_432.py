from companyos_phase417_432 import VentureBuildIntake, TestRepairLoop, VentureExecutionRuntime

def test_incomplete_packet_rejected():
    assert VentureBuildIntake().accept({"success":True})["accepted"] is False

def test_repair_loop():
    assert TestRepairLoop().evaluate({"passed":False},1,3)["action"] == "repair"
    assert TestRepairLoop().evaluate({"passed":False},3,3)["action"] == "halt"

def test_runtime():
    s = VentureExecutionRuntime().status()
    assert s["status"] == "phase432_autonomous_build_bridge_ready"
    assert s["automatic_irreversible_launch"] is False
