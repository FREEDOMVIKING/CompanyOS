from companyos.runtime import provider_connector_router as p

def test_provider_status_exposes_public_research_mesh(monkeypatch):
    monkeypatch.setattr(
        p.pab,
        "discover_credentials",
        lambda: ({}, {
            "cloudflare_workers_ai":{},
            "tavily":{},
            "brave_search":{},
            "groq":{},
            "gemini":{},
            "huggingface":{},
            "openai":{},
        }),
    )
    monkeypatch.setattr(
        p,
        "discover_cf_account",
        lambda: {"available":False,"reason":"test"},
    )
    status=p.provider_status()
    assert "public_research_mesh" in status["capabilities"]["web_search"]

def test_public_research_mesh_deduplicates(monkeypatch):
    monkeypatch.setattr(
        p,
        "gdelt_search",
        lambda q,max_results=5:{
            "provider":"gdelt",
            "results":[
                {"title":"A","url":"https://example.com/a","content":"news"},
            ],
            "result_count":1,
        },
    )
    monkeypatch.setattr(
        p,
        "wikipedia_search",
        lambda q,max_results=5:{
            "provider":"wikipedia",
            "results":[
                {"title":"A duplicate","url":"https://example.com/a","content":"wiki"},
                {"title":"B","url":"https://example.com/b","content":"wiki"},
            ],
            "result_count":2,
        },
    )
    monkeypatch.setattr(
        p,
        "github_public_search",
        lambda q,max_results=5:{
            "provider":"github_public_rest",
            "results":[
                {"name":"repo","url":"https://github.com/example/repo","description":"repo"},
            ],
            "result_count":1,
        },
    )

    out=p.public_research_mesh_search("test",10)
    assert out["provider"]=="public_research_mesh"
    assert out["result_count"]==3
    assert len({x.get("url") for x in out["results"]})==3

def test_search_web_falls_back_to_public_mesh(monkeypatch):
    monkeypatch.setattr(
        p,
        "provider_status",
        lambda:{
            "capabilities":{
                "web_search":["public_research_mesh"],
            }
        },
    )
    monkeypatch.setattr(
        p,
        "public_research_mesh_search",
        lambda q,max_results=5:{
            "provider":"public_research_mesh",
            "results":[{"title":"live","url":"https://example.com"}],
            "result_count":1,
        },
    )
    out=p.search_web("test",5)
    assert out["provider"]=="public_research_mesh"
    assert out["result_count"]==1
    assert out["attempts"][-1]["status"]=="success"
