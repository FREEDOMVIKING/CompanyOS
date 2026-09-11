from companyos.expansionops import ExpansionRadar, PortfolioSynergyEngine, ExpansionAuthorityBoundary

def test_radar():
    assert ExpansionRadar().rank([{"demand":1,"strategic_fit":1,"margin_potential":1,"speed_to_market":1,"risk":0}])[0]["expansion_score"]==1

def test_synergy():
    rows=PortfolioSynergyEngine().evaluate([
        {"venture_id":"a","capabilities":["sales"],"customer_segments":["smb"]},
        {"venture_id":"b","capabilities":["sales"],"customer_segments":["enterprise"]}
    ])
    assert rows[0]["synergy_score"]>=1

def test_boundary():
    assert ExpansionAuthorityBoundary().evaluate({"kind":"sign_partner_agreement"})["requires_approval"]
