from companyos.runtime import targeted_public_evidence_search_v2 as v2

def test_ddg_lite_parser(monkeypatch):
    body='<a rel="nofollow" href="https://vendor.example/pricing">Construction pricing</a>'
    monkeypatch.setattr(v2.base,"_request",lambda *a,**k:(body,"text/html"))
    rows=v2.search_ddg_lite("construction pricing")
    assert len(rows)==1
    assert rows[0]["url"]=="https://vendor.example/pricing"

def test_bing_parser(monkeypatch):
    body='<li class="b_algo"><h2><a href="https://vendor.example/case">Case Study</a></h2></li>'
    monkeypatch.setattr(v2.base,"_request",lambda *a,**k:(body,"text/html"))
    rows=v2.search_bing("construction case study")
    assert len(rows)==1
    assert rows[0]["url"]=="https://vendor.example/case"

def test_search_all_deduplicates(monkeypatch):
    def a(q): return [{"url":"https://a.example/x","title":"A","domain":"a.example","provider":"a"}]
    def b(q): return [
        {"url":"https://a.example/x","title":"A2","domain":"a.example","provider":"b"},
        {"url":"https://b.example/y","title":"B","domain":"b.example","provider":"b"},
    ]
    monkeypatch.setattr(v2,"PROVIDERS",(("a",a),("b",b)))
    rows,diag=v2.search_all("q")
    assert len(rows)==2
    assert len(diag)==2

def test_expanded_queries_are_not_all_quoted():
    candidate={
        "market":"construction",
        "target_customer":"concrete contractors",
        "problem":"estimating workflow",
        "offer":"AI bid workflow automation",
    }
    q=v2.expanded_queries(candidate,"pricing")
    assert len(q)>=4
    assert any('"' not in x for x in q)
