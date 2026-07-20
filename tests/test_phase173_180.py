from companyos_phase173_180 import WorldModel,CounterfactualEngine,SkillFactory,MetricSentinel,SovereignOrchestrator
def test_world(): assert WorldModel().update([],[{"topic":"x","signal":.8,"confidence":1}])[0]["belief"]==.8
def test_counterfactual(): assert CounterfactualEngine().rank([{"name":"x","upside":1,"probability":1}])[0]["name"]=="x"
def test_skill_factory(): assert SkillFactory().propose([{"workflow":"x"}],1)[0]["autonomous_generation_allowed"]
def test_metric(): assert MetricSentinel().inspect([{"value":2,"baseline":1,"tolerance":.2}])
def test_orchestrator(): assert SovereignOrchestrator().run({})["self_directed_orchestration"]
