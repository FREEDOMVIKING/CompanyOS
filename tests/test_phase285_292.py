from companyos_phase285_292 import ImprovementStateStore, PausePolicy, ResumeController

def test_state_store(tmp_path):
    s = ImprovementStateStore(tmp_path)
    state = s.load()
    state["cycles_completed"] = 1
    s.save(state)
    assert s.load()["cycles_completed"] == 1

def test_pause_policy():
    assert PausePolicy().evaluate({"paused": True}, {})["pause"] is True

def test_resume_controller(tmp_path):
    ctl = ResumeController(tmp_path)
    ctl.pause()
    assert ctl.status()["paused"] is True
    ctl.resume()
    assert ctl.status()["paused"] is False
