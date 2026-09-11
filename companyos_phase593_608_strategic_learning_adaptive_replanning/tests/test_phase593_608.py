from companyos_phase593_608 import LessonExtractor, StrategyAdjuster, ConfidenceUpdater

def test_lessons():
    lessons = LessonExtractor().extract("operations",{"activation_rate":0.05},"operations")
    assert "weak_activation" in lessons

def test_strategy_adjustment():
    strategy = StrategyAdjuster().adjust({},["weak_retention"])
    assert "revisit_problem_solution_fit" in strategy["changes"]

def test_confidence():
    assert ConfidenceUpdater().update(0.5,["weak_activation"]) < 0.5
