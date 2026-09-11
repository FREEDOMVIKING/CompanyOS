from companyos_phase337_352 import ProblemClusterer, MarketGapDetector, OpportunityConfidence

def test_clusterer():
    clusters = ProblemClusterer().cluster([
        {"statement":"Manual work is slow","source":"x"}
    ])
    assert clusters

def test_gap_detector():
    gaps = MarketGapDetector().detect([{"theme":"time_waste","count":2,"problems":[]}], [])
    assert gaps[0]["gap_strength"] > 0

def test_confidence():
    opp = {"evidence":["a","b"],"gap":{"pain_evidence_count":3}}
    assert OpportunityConfidence().score(opp, 2) > 0
