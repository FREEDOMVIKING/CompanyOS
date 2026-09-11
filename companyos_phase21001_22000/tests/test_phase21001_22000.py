from companyos.treasuryops import TreasuryPolicy, TreasuryRiskEngine

def test_reserve_floor_blocks():
    p = TreasuryPolicy(allow_autonomous_transfers=True, reserve_floor=250)
    r = TreasuryRiskEngine().evaluate(
        amount=800,
        balance=1000,
        destination_allowed=True,
        daily_spend=0,
        daily_loss=0,
        policy=p
    )
    assert r["hard_block"] is True

def test_allowlist_blocks():
    p = TreasuryPolicy(allow_autonomous_transfers=True, require_allowlist=True)
    r = TreasuryRiskEngine().evaluate(
        amount=10,
        balance=1000,
        destination_allowed=False,
        daily_spend=0,
        daily_loss=0,
        policy=p
    )
    assert r["hard_block"] is True

def test_default_not_autonomous():
    assert TreasuryPolicy().allow_autonomous_transfers is False
