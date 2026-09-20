from companyos.runtime.verified_web_prospect_discovery import (
    _query_variants,
    rank_search_candidates,
)

def copy():
    return {
        "title":"Local Contractor Bid Organizer",
        "audience":"construction contractors",
        "description":"Organize bids and estimates for contractors",
    }

def test_queries_bias_toward_official_contacts_and_away_from_content():
    q=_query_variants("local_contractor_bid_organizer",copy())
    assert len(q)>=4
    assert any('"contact us"' in x.lower() for x in q)
    assert any("-blog" in x.lower() for x in q)

def test_content_pages_are_removed_before_crawl():
    rows=[
        {"title":"20 Contractor Email Examples","url":"https://example.com/blog/contractor-email-examples"},
        {"title":"ABC Construction","url":"https://abcconstruction.example/"},
    ]
    ranked=rank_search_candidates(rows,copy())
    assert len(ranked)==1
    assert ranked[0]["candidate_host"]=="abcconstruction.example"

def test_duplicate_host_is_collapsed():
    rows=[
        {"title":"ABC Construction","url":"https://abcconstruction.example/"},
        {"title":"ABC Construction Contact","url":"https://abcconstruction.example/contact"},
    ]
    ranked=rank_search_candidates(rows,copy())
    assert len(ranked)==1

def test_known_directory_is_rejected():
    rows=[
        {"title":"Contractors on Yelp","url":"https://www.yelp.com/search?find_desc=contractor"},
        {"title":"Real Builder Group","url":"https://realbuilder.example/"},
    ]
    ranked=rank_search_candidates(rows,copy())
    assert all("yelp.com" not in x["candidate_host"] for x in ranked)
