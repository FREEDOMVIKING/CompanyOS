from companyos.runtime import adaptive_offload_calibration_resumer as r


def test_waits_when_daily_slots_are_exhausted(monkeypatch):
    monkeypatch.setattr(r.scheduler,"dispatched_today",lambda:30)
    monkeypatch.setattr(r.scheduler,"DAILY_CAP",30)
    monkeypatch.setattr(r.scheduler,"active_jobs",lambda:[])
    monkeypatch.setattr(r.calibration,"STATE",r.Path("/definitely/missing/state.json"))
    d=r.decide()
    assert d["action"]=="wait"
    assert d["reason"]=="daily_dispatch_capacity"
    assert d["dispatch_slots_available"]==0


def test_runs_when_four_slots_are_available(monkeypatch):
    monkeypatch.setattr(r.scheduler,"dispatched_today",lambda:20)
    monkeypatch.setattr(r.scheduler,"DAILY_CAP",30)
    monkeypatch.setattr(r.scheduler,"active_jobs",lambda:[])
    monkeypatch.setattr(r.calibration,"STATE",r.Path("/definitely/missing/state.json"))
    d=r.decide()
    assert d["action"]=="run_calibration"
    assert d["dispatch_slots_available"]==10


def test_does_not_repeat_completed_calibration(monkeypatch,tmp_path):
    state=tmp_path/"cal.json"
    state.write_text('{"status":"completed"}',encoding="utf-8")
    monkeypatch.setattr(r.calibration,"STATE",state)
    monkeypatch.setattr(r.scheduler,"dispatched_today",lambda:0)
    monkeypatch.setattr(r.scheduler,"DAILY_CAP",30)
    d=r.decide()
    assert d["action"]=="sleep_completed"
