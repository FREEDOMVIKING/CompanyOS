from companyos_phase101_108 import EconomicsEngine,RecoveryDirector,AutonomousCEOLoop
def test_economics_no_fund_movement(): assert EconomicsEngine().analyze(10,2,10,5)["funds_moved"] is False
def test_critical_recovery_escalates(): assert RecoveryDirector().direct({"severity":"critical"})["requires_attention"] is True
def test_loop_bounded(): assert AutonomousCEOLoop().run({})["external_action_taken"] is False
