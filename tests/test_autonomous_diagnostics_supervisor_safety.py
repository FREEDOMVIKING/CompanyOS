from pathlib import Path

import companyos.runtime.autonomous_diagnostics as ad


def test_diagnostics_uses_shared_runtime_root():
    assert ad.RT == Path.home() / ".companyos_runtime"
    assert ad.STOP == ad.RT / "autonomous_diagnostics.stop"


def test_diagnostics_never_restarts_parent_supervisor(monkeypatch, tmp_path):
    monkeypatch.setattr(ad, "RT", tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("autonomous diagnostics must not invoke a supervisor restart")

    monkeypatch.setattr(ad.subprocess, "run", forbidden)

    result = ad.apply(
        [{"repair": "supervisor_restart", "reason": {"service": "x"}}]
    )

    assert result
    assert result[0]["ok"] is True
    assert result[0]["executed_restart"] is False
    assert result[0]["action"] == "deferred_to_supervisor_control_plane"

    request = tmp_path / "diagnostics_supervisor_recovery_requested.json"
    assert request.exists()

def test_diagnostics_atomic_writes_parseable_json(tmp_path):
    import json
    p = tmp_path / "state.json"
    ad.atomic(p, {"ok": True, "nested": {"n": 1}})
    text = p.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == {"ok": True, "nested": {"n": 1}}
