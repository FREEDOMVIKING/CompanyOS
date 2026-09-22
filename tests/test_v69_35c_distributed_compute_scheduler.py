import json
from companyos.runtime import distributed_compute_scheduler as sched

def test_adaptive_shards():
    assert sched.shard_count(1)==1
    assert sched.shard_count(2)<=2
    assert sched.shard_count(4)<=4
    assert sched.shard_count(20)<=8

def test_validation_backlog_filters_inactive(monkeypatch,tmp_path):
    p=tmp_path/"validation.json"
    p.write_text(json.dumps({"experiments":[
        {"portfolio_active":True,"status":"planned","query":"live query","candidate_name":"A","experiment_id":"a"},
        {"portfolio_active":False,"status":"planned","query":"inactive query","candidate_name":"B","experiment_id":"b"}
    ]}),encoding="utf-8")
    monkeypatch.setattr(sched,"VALIDATION_QUEUE",p)
    rows=sched.validation_backlog()
    assert len(rows)==1
    assert rows[0]["query"]=="live query"

def test_priority_increases_with_backlog():
    assert sched.priority_score(10,4)>sched.priority_score(2,1)

def test_can_enqueue_respects_inflight(monkeypatch):
    monkeypatch.setattr(sched,"active_jobs",lambda:[{"status":"running"}]*sched.MAX_INFLIGHT)
    ok,reason=sched.can_enqueue()
    assert ok is False
    assert reason=="inflight_cap"

def test_daily_cap_blocks(monkeypatch):
    monkeypatch.setattr(sched,"active_jobs",lambda:[])
    monkeypatch.setattr(sched,"dispatched_today",lambda:sched.DAILY_CAP)
    monkeypatch.setattr(sched,"last_dispatch_unix",lambda:0.0)
    monkeypatch.setattr(sched.pool,"gh_ready",lambda:{"ready":True})
    ok,reason=sched.can_enqueue()
    assert ok is False
    assert reason=="daily_cap"

def test_validation_queue_uses_adaptive_shards(monkeypatch):
    monkeypatch.setattr(
        sched.pool,
        "enqueue",
        lambda kind,payload,shards,dedupe_key:{
            "job_id":"x","kind":kind,"payload":payload,"shards":shards,"dedupe_key":dedupe_key
        },
    )
    monkeypatch.setattr(sched,"record_dispatch",lambda *a,**k:None)
    rows=[{"query":f"q{i}","candidate_name":"A","experiment_id":f"e{i}"} for i in range(7)]
    job=sched.queue_validation(rows)
    assert job["kind"]=="research"
    assert job["shards"]==sched.shard_count(7)
    assert job["shards"]<=8

def test_scheduler_never_enables_external_actions(monkeypatch,tmp_path):
    monkeypatch.setattr(sched,"STATE",tmp_path/"state.json")
    monkeypatch.setattr(sched,"VALIDATION_QUEUE",tmp_path/"validation.json")
    monkeypatch.setattr(sched,"EVIDENCE_QUEUE",tmp_path/"evidence.json")
    monkeypatch.setattr(sched,"HISTORY",tmp_path/"history.json")
    monkeypatch.setattr(sched,"active_jobs",lambda:[])
    monkeypatch.setattr(sched,"can_enqueue",lambda:(False,"test"))
    monkeypatch.setattr(sched.pool,"gh_ready",lambda:{"ready":True,"reason":"ok"})
    monkeypatch.setattr(sched,"effectiveness",lambda:{})
    out=sched.once()
    assert out["external_messages_allowed"] is False
    assert out["financial_actions_allowed"] is False
    assert out["deployments_allowed"] is False
    assert out["account_creation_allowed"] is False
