from companyos_phase197_204 import GoalContinuityEngine,AutonomousBuilder,ValidationEngine,IdleWorkGenerator,AlwaysOnCEO
def test_continuity(): assert GoalContinuityEngine().reconcile([{"goal":"x"}],[])[0]["carry_forward"]
def test_builder(): assert AutonomousBuilder().next({"spec_ready":True})["action"]=="implement"
def test_validation(): assert ValidationEngine().evaluate({})["autonomous_next_action"]
def test_idle(): assert len(IdleWorkGenerator().generate(0,3))==3
def test_ceo(): assert AlwaysOnCEO().tick({})["always_on_ceo"]
