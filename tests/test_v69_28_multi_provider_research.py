import time

from companyos.runtime import multi_provider_research_pipeline as mpr
from companyos.runtime import provider_connector_router as pcr

def test_candidate_rotation_prefers_distinct_candidates():
    tasks=[
        {"candidate_name":"a","created_at":1,"provider_last_attempt_at_unix":0},
        {"candidate_name":"a","created_at":2,"provider_last_attempt_at_unix":0},
        {"candidate_name":"b","created_at":3,"provider_last_attempt_at_unix":0},
    ]
    chosen=mpr._candidate_diverse_tasks(tasks,2)
    assert {x["candidate_name"] for x in chosen}=={"a","b"}

def test_no_web_provider_defers_only_task_not_global_runtime(monkeypatch):
    monkeypatch.setattr(
        pcr,
        "provider_status",
        lambda:{
            "capabilities":{
                "web_search":[],
                "llm_inference":["cloudflare_workers_ai"],
                "public_code_research":["github_public_rest"],
            }
        },
    )
    monkeypatch.setattr(
        mpr,
        "_candidate",
        lambda name:(object(),{"name":name,"market":"concrete estimating"}),
    )

    queue={
        "tasks":[{
            "task_id":"t1",
            "candidate_name":"concrete_ai",
            "requirement":"pricing",
            "guidance":"pricing",
            "status":"research_required",
            "created_at":1.0,
        }]
    }

    out=mpr.cycle(queue=queue,persist_queue=False,max_tasks=1)
    task=queue["tasks"][0]

    assert out["global_runtime_blocked"] is False
    assert out["deferred_task_count"]==1
    assert task["status"]=="research_required"
    assert task["research_deferred_reason"]=="no_web_search_provider"
    assert task["global_runtime_blocked"] is False

def test_query_text_does_not_count_as_evidence():
    anchors={"concrete","estimating"}
    row={
        "url":"https://example.com",
        "title":"Generic pricing page",
        "content":"Monthly price is 20 dollars.",
        "search_query":"concrete estimating software",
    }
    assert mpr._row_valid(row,anchors,"pricing") is False

def test_actual_result_requires_two_candidate_anchors_and_requirement_term():
    anchors={"concrete","estimating","contractor"}
    row={
        "url":"https://example.com",
        "title":"Concrete estimating platform pricing",
        "content":"Contractors can subscribe for a monthly price.",
    }
    assert mpr._row_valid(row,anchors,"pricing") is True

def test_cloudflare_is_first_internal_inference_route(monkeypatch):
    monkeypatch.setattr(
        pcr,
        "provider_status",
        lambda:{
            "capabilities":{
                "llm_inference":["cloudflare_workers_ai","openai"]
            }
        },
    )
    monkeypatch.setattr(pcr,"_cooldown_remaining",lambda name:0.0)
    monkeypatch.setattr(pcr,"_mark_provider_success",lambda *a,**k:None)
    monkeypatch.setattr(pcr,"_mark_provider_failure",lambda *a,**k:None)
    monkeypatch.setattr(
        pcr,
        "cloudflare_infer",
        lambda prompt,max_tokens=160:{
            "provider":"cloudflare_workers_ai",
            "model":"test",
            "text":"READY",
            "latency_seconds":0.1,
        },
    )
    monkeypatch.setattr(
        pcr,
        "openai_internal_infer",
        lambda *a,**k:(_ for _ in ()).throw(AssertionError("openai should not run")),
    )

    out=pcr.infer_text("test",32)
    assert out["provider"]=="cloudflare_workers_ai"

def test_deferred_task_becomes_due_after_window():
    now=time.time()
    task={"research_deferred_until_unix":now-1}
    assert mpr._due(task,now) is True
