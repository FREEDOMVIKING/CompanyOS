from companyos_phase889_904 import RevalidationRoundScheduler,DiminishingReturnsDetector,BoundedExhaustionPolicy
def test_schedule():
    assert RevalidationRoundScheduler().next_round(1,"REVISE",3)["run"] is True
def test_diminishing():
    h=[{"confidence":.6},{"confidence":.61},{"confidence":.615}]
    assert DiminishingReturnsDetector().evaluate(h)["diminishing"] is True
def test_exhaustion():
    assert BoundedExhaustionPolicy().decide(.7)["action"]=="review"
