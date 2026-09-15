from pathlib import Path

def test_launcher_bootstraps_repo_path():
    p=Path("scripts/companyos_workforce_execute")
    s=p.read_text()
    assert "Path(__file__).resolve().parents[1]" in s
    assert "sys.path.insert(0, repo_s)" in s

def test_bridge_uses_factory_cycle():
    p=Path("companyos/runtime/adaptive_workforce_execution_bridge.py")
    s=p.read_text()
    assert "factory.cycle" in s
    assert "factory.evaluate" not in s
