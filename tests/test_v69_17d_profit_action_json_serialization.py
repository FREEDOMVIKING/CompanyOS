import json
from companyos.runtime import profit_to_action_closure as pta

def test_atomic_writes_valid_json_with_real_newline(tmp_path):
    p=tmp_path/"state.json"
    pta.atomic(p,{"ok":True,"n":1})
    raw=p.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert not raw.endswith("\\n")
    assert json.loads(raw)=={"ok":True,"n":1}

def test_emit_writes_real_jsonl_records(tmp_path,monkeypatch):
    events=tmp_path/"events.jsonl"
    monkeypatch.setattr(pta,"EVENTS",events)
    pta.emit("one",value=1)
    pta.emit("two",value=2)
    raw=events.read_text(encoding="utf-8")
    lines=raw.splitlines()
    assert len(lines)==2
    rows=[json.loads(line) for line in lines]
    assert [row["kind"] for row in rows]==["one","two"]

def test_isolated_cycle_persists_parseable_state(tmp_path,monkeypatch):
    monkeypatch.setattr(pta,"QUEUE",tmp_path/"queue.json")
    monkeypatch.setattr(pta,"STATE",tmp_path/"state.json")
    monkeypatch.setattr(pta,"EVENTS",tmp_path/"events.jsonl")
    monkeypatch.setattr(pta,"STOP",tmp_path/"STOP_CONTINUOUS")
    pta.QUEUE.write_text('{"actions":[]}\n',encoding="utf-8")
    out=pta.cycle()
    assert out["status"]=="no_new_executable_packet"
    saved=json.loads(pta.STATE.read_text(encoding="utf-8"))
    assert saved["healthy"] is True
    assert saved["last_cycle_unix"] > 0
