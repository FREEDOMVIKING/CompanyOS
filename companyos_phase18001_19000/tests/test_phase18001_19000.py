from companyos.cycleops import OutcomeClassifier, CycleVerifier, ApprovalDeferment

def test_completed():
    o = OutcomeClassifier().classify({"job_id":"x"}, {"success":True})
    assert o["state"] == "completed"
    assert o["resolved"] is True

def test_approval_deferred():
    job = {"job_id":"x","payload":{"requires_approval":True}}
    r = ApprovalDeferment().normalize(job, {"success":False})
    o = OutcomeClassifier().classify(job, r)
    assert o["state"] == "deferred_for_approval"
    assert o["resolved"] is True

def test_cycle_verified_when_all_resolved():
    v = CycleVerifier()
    rows = [
        {"verification":v.verify_execution({"job_id":"1"},{"success":True})},
        {"verification":v.verify_execution(
            {"job_id":"2","payload":{"requires_approval":True}},
            {"success":False,"blocked":True,"reason":"approval_required","requires_approval":True}
        )}
    ]
    s = v.summarize_cycle(rows)
    assert s["cycle_verified"] is True
