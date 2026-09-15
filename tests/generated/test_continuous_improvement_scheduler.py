from companyos.runtime.continuous_improvement_scheduler import ContinuousImprovementScheduler

def test_protected(tmp_path):
    c=ContinuousImprovementScheduler(tmp_path)
    assert c.protected("companyos/finance/live_transfer.py")
    assert not c.protected("candidate_qualification")

def test_new_specialist_selected(tmp_path):
    c=ContinuousImprovementScheduler(tmp_path)
    b={"id":"market_evidence","priority":80,"hits":3,"sources":[]}
    selected,action=c.choose([b],{"workers":{}})
    assert selected["id"]=="market_evidence"
    assert action=="build_new_specialist"

def test_permanent_requires_repeated_evidence(tmp_path):
    c=ContinuousImprovementScheduler(tmp_path)
    reg={"workers":{}}
    b={"id":"market_evidence","priority":80,"hits":3,"sources":[]}
    for _ in range(3):
        w=c.update_worker(b,"build_new_specialist",reg)
    assert w["status"]=="permanent"
    assert w["successes"]==3

def test_no_invented_profit(tmp_path):
    c=ContinuousImprovementScheduler(tmp_path)
    reg={"workers":{}}
    b={"id":"revenue_evidence","priority":80,"hits":2,"sources":[]}
    w=c.update_worker(b,"build_new_specialist",reg)
    assert w["attributed_profit"]==0.0
