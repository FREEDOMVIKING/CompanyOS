from companyos_phase657_672 import BurnRunway, ROIScore, AllocationPolicy

def test_runway():
    r=BurnRunway().calculate({
        "variable_costs":1000,"fixed_costs":1000,"acquisition_spend":0,
        "mrr":1000,"cash_available":12000
    })
    assert r["runway_months"]==12.0

def test_roi():
    assert ROIScore().score({"incremental_value":200,"resource_cost":100})>5

def test_allocation_gate():
    d=AllocationPolicy().decide({
        "roi_score":8,"resource_efficiency":2,"has_anomaly":False,"runway_months":12
    })
    assert d["decision"]=="prepare_scale_review"
    assert d["automatic_financial_transfer"] is False
