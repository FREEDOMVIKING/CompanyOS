from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts" / "companyos_workforce_loop"

def test_launcher_adds_repo_root_before_companyos_import():
    src = LAUNCHER.read_text()
    assert 'Path(__file__).resolve().parents[1]' in src
    assert 'sys.path.insert(0, repo)' in src
    assert src.index('sys.path.insert(0, repo)') < src.index(
        'from companyos.runtime.autonomous_workforce_loop import cycle, run'
    )

def test_direct_script_can_resolve_companyos_from_outside_repo():
    # Reproduce the failure mode: execute the scripts/ file with cwd outside
    # the repository, but only import/compile it rather than running a live cycle.
    code = f"""
import runpy
p={str(LAUNCHER)!r}
ns=runpy.run_path(p, run_name='companyos_launcher_import_test')
assert callable(ns['cycle'])
assert callable(ns['run'])
"""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    cp = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT.parent),
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert cp.returncode == 0, cp.stdout + cp.stderr
