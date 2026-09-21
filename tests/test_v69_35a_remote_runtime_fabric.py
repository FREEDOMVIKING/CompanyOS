import json
from companyos.runtime import remote_runtime_fabric as rrf
from companyos.runtime import remote_research_worker as rrw

def test_add_node_does_not_store_password_or_token(monkeypatch,tmp_path):
    p=tmp_path/"inventory.json"; monkeypatch.setattr(rrf,"INVENTORY",p)
    out=rrf.add_node("w1","oracle","research_worker","ubuntu@203.0.113.10")
    raw=p.read_text(encoding="utf-8").lower()
    assert out["role"]=="research_worker"
    assert "password" not in raw
    assert "api_token" not in raw

def test_worker_roles_exclude_standby(monkeypatch,tmp_path):
    p=tmp_path/"inventory.json"; monkeypatch.setattr(rrf,"INVENTORY",p)
    p.write_text(json.dumps({"nodes":[
        {"name":"a","provider":"oracle","role":"research_worker","ssh_target":"u@h","enabled":True,"capacity_score":2},
        {"name":"b","provider":"google","role":"standby","ssh_target":"u@h2","enabled":True,"capacity_score":10}
    ]}),encoding="utf-8")
    assert [x["name"] for x in rrf.worker_nodes()]==["a"]

def test_remote_worker_read_only(monkeypatch):
    monkeypatch.setattr(rrw.pcr,"search_web",lambda q,max_results=8:{
        "provider":"public_research_mesh","results":[{"url":"https://example.com"}],
        "result_count":1,"attempts":[]
    })
    out=rrw.search("test",5)
    assert out["healthy"] is True
    assert out["external_messages_sent"] is False
    assert out["financial_actions_performed"] is False
    assert out["deployments_performed"] is False

def test_state_sync_allowlist_excludes_env_and_keys(monkeypatch,tmp_path):
    rt=tmp_path/"runtime"; rt.mkdir()
    (rt/"evidence_acquisition_queue.json").write_text("{}",encoding="utf-8")
    (rt/".env").write_text("SECRET=bad",encoding="utf-8")
    (rt/"private_key").write_text("bad",encoding="utf-8")
    monkeypatch.setattr(rrf,"RT",rt)
    names={x.name for x in rrf.state_members()}
    assert "evidence_acquisition_queue.json" in names
    assert ".env" not in names
    assert "private_key" not in names
