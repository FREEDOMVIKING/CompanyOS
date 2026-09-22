import base64, json
from companyos.runtime import github_actions_worker as gaw
from companyos.runtime import github_actions_worker_pool as pool

def test_payload_decode_roundtrip():
    payload={"queries":[{"query":"a"},{"query":"b"}]}
    encoded=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    assert gaw.decode_payload(encoded)==payload

def test_shards_are_complete_and_nonoverlapping():
    items=list(range(19))
    groups=[gaw.shard_items(items,i,4) for i in range(4)]
    flat=[x for g in groups for x in g]
    assert sorted(flat)==items
    assert len(flat)==len(set(flat))

def test_smoke_cannot_take_external_actions():
    out=gaw.execute("j","smoke",{},0,2)
    assert out["healthy"] is True
    assert out["external_messages_sent"] is False
    assert out["financial_actions_performed"] is False
    assert out["deployments_performed"] is False

def test_enqueue_dedupe(monkeypatch,tmp_path):
    monkeypatch.setattr(pool,"QUEUE",tmp_path/"q.json")
    a=pool.enqueue("research",{"queries":[{"query":"x"}]},2,"same")
    b=pool.enqueue("research",{"queries":[{"query":"x"}]},2,"same")
    assert a["job_id"]==b["job_id"]

def test_validation_seed(monkeypatch,tmp_path):
    p=tmp_path/"v.json"
    p.write_text(json.dumps({"experiments":[{
        "portfolio_active":True,"status":"planned","query":"example demand",
        "candidate_name":"Example","requirement":"buyer_demand","experiment_id":"e1"
    }]}))
    monkeypatch.setattr(pool,"VALIDATION_QUEUE",p)
    monkeypatch.setattr(pool,"QUEUE",tmp_path/"jobs.json")
    job=pool.seed_validation()
    assert job["kind"]=="research"
    assert job["payload"]["queries"][0]["candidate_name"]=="Example"

def test_result_import_attaches_evidence(monkeypatch,tmp_path):
    monkeypatch.setattr(pool,"CANONICAL",tmp_path/"canonical")
    monkeypatch.setattr(pool,"EVIDENCE_QUEUE",tmp_path/"evidence.json")
    job={"job_id":"j1","run_id":1,"kind":"research"}
    shards=[{"outcomes":[{
        "query":"example","status":"success","provider":"public_research_mesh",
        "metadata":{"candidate_name":"Example","requirement":"buyer_demand"},
        "results":[{"url":"https://a.example/x"},{"url":"https://b.example/y"}]
    }]}]
    out=pool.import_results(job,shards)
    assert out["imported_artifacts"]==1
    assert out["attached_evidence"]==1
