from companyos.runtime.verified_web_prospect_discovery import _query_variants

def test_query_variants_are_multiple():
    q=_query_variants("local_contractor_bid_organizer",{
        "title":"Local Contractor Bid Organizer",
        "audience":"construction contractors",
        "description":"Organize bids and estimates",
    })
    assert len(q) >= 3

def test_audience_drives_search():
    q=_query_variants("local_contractor_bid_organizer",{
        "title":"Local Contractor Bid Organizer",
        "audience":"construction contractors",
        "description":"Organize bids and estimates",
    })
    assert any("construction contractors" in x.lower() for x in q)
