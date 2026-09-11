from companyos_phase841_856 import DecisionThreshold, RevalidationPolicy, FalsePositiveGuard

def test_go():
    assert DecisionThreshold().decide(0.8,True,True)["decision"]=="GO"

def test_revise():
    assert RevalidationPolicy().next("REVISE",0)["revalidate"] is True

def test_false_positive_guard():
    packet={"confidence":0.8,"evidence":[
        {"source_class":"official"},
        {"source_class":"public_web"},
        {"source_class":"reputable_news"},
    ]}
    assert FalsePositiveGuard().evaluate(packet)["passed"] is True
