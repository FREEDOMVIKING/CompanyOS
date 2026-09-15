from companyos.runtime.verified_outcome_scoring import VerifiedOutcomeScorer

def test_activity_alone_not_permanent(tmp_path):
    s=VerifiedOutcomeScorer(tmp_path)
    w={
        "role":"candidate_qualification",
        "jobs":3,
        "successes":3,
        "failures":0,
        "status":"permanent",
    }
    r=s.evaluate_worker(w,[])
    assert r["status"]=="probation"
    assert r["verified_outcome_score"]==0

def test_real_outcomes_below_threshold_stay_probation(tmp_path):
    s=VerifiedOutcomeScorer(tmp_path)
    w={"role":"candidate_qualification","jobs":3,"successes":3,"failures":0}
    sig=[
        {"class":"opportunity_advanced","weight":20,"source":"a"},
        {"class":"verified_evidence","weight":20,"source":"b"},
    ]
    r=s.evaluate_worker(w,sig)
    assert r["verified_outcome_score"]==40
    assert r["verified_score"]==55.0
    assert r["status"]=="probation"

def test_sufficient_real_outcomes_can_promote(tmp_path):
    s=VerifiedOutcomeScorer(tmp_path)
    w={"role":"candidate_qualification","jobs":3,"successes":3,"failures":0}
    sig=[
        {"class":"opportunity_advanced","weight":20,"source":"a"},
        {"class":"verified_evidence","weight":20,"source":"b"},
        {"class":"verified_evidence","weight":20,"source":"c"},
    ]
    r=s.evaluate_worker(w,sig)
    assert r["verified_outcome_score"]==60
    assert r["verified_score"]==70.0
    assert r["status"]=="permanent"

def test_revenue_role_does_not_use_deployment_as_revenue(tmp_path):
    s=VerifiedOutcomeScorer(tmp_path)
    w={"role":"revenue_evidence","jobs":3,"failures":0}
    sig=[{"class":"deployment_or_reachability","weight":15,"source":"x"}]
    r=s.evaluate_worker(w,sig)
    assert r["verified_outcome_score"]==0
    assert r["status"]=="probation"
