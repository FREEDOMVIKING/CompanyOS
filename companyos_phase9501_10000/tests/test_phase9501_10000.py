from companyos.productionruntime import StartupPreflight, ContinuousCompanyCycle, MissionRouter

def test_preflight():
    assert StartupPreflight().evaluate({
        "state_store":True,"checkpoint":True,"queue":True,"memory":True,
        "approval_queue":True,"health":True,"config":True})["passed"]

def test_cycle():
    assert ContinuousCompanyCycle().plan("build")["next_stage"]=="launch"

def test_router():
    assert MissionRouter().route({"mission_type":"finance"})["department"]=="finance"
