from companyos_phase937_1000 import EvidenceRescoreEngine,ValidationConvergenceEngine,ReleaseCandidateGate
def test_rescore():
    p={"evidence":[{"id":"1","source_class":"official","tags":["problem","pricing"]}]}
    assert EvidenceRescoreEngine().score(p)["problem_evidence"]>0
def test_go():
    v={"scores":{"validation_confidence":.8},"false_positive_guard":{"passed":True},"contradictions":{"resolved":True}}
    assert ValidationConvergenceEngine().decide(v)["decision"]=="GO"
def test_release_gate():
    assert ReleaseCandidateGate().evaluate({"build_success":True,"tests_passed":True},[{"passed":True}],True)["passed"] is True
