from companyos_phase189_196 import IntentEngine,ExperimentLoop,AutonomousArchitect,GrowthFlywheel,CompanyKernel
def test_intent(): assert IntentEngine().generate("x",{})[0]["autonomous"]
def test_experiment(): assert ExperimentLoop().next({"stage":"measure"})["stage"]=="learn"
def test_architect(): assert AutonomousArchitect().evaluate({"kind":"add_tests"})["autonomous_change_allowed"]
def test_growth(): assert GrowthFlywheel().evaluate({})["autonomous"]
def test_kernel(): assert CompanyKernel().tick({})["persistent_kernel"]
