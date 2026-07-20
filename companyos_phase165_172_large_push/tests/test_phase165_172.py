from companyos_phase165_172 import ObjectiveTree,ExecutionSupervisor,VentureLifecycle,CapacityManager,CompanyDaemon
def test_tree(): assert ObjectiveTree().build("x",1)["children"]
def test_retry(): assert ExecutionSupervisor().supervise([{"status":"failed","attempts":0}])[0]["autonomous"]
def test_lifecycle(): assert VentureLifecycle().decide({"traction":.6,"evidence":.8,"risk":.1})["action"]=="grow"
def test_capacity(): assert round(sum(CapacityManager().allocate(10).values()),3)==10
def test_daemon(): assert CompanyDaemon().tick({})["persistent_heartbeat"]
