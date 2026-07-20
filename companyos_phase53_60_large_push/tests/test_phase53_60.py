from companyos_phase53_60 import ApprovalGuard, AgentRouter, PortfolioManager

def test_guard_blocks_unapproved_high_impact():
    assert ApprovalGuard().evaluate({"type":"purchase"})["allowed"] is False

def test_router():
    assert AgentRouter().route({"category":"build"}) == "builder_agent"

def test_portfolio_sort():
    rows = PortfolioManager().rank([
        {"name":"low","expected_value":1,"confidence":.2,"risk":.9},
        {"name":"high","expected_value":5,"confidence":.9,"risk":.1},
    ])
    assert rows[0]["name"] == "high"
