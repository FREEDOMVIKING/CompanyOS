from companyos_phase69_76 import ValidationEngine, LaunchPlanner
def test_uncertain_without_evidence():
    assert ValidationEngine().validate([])["verdict"]=="insufficient_evidence"
def test_launch_is_planning_only():
    assert LaunchPlanner().plan({"name":"x"})["external_action_taken"] is False
