from pathlib import Path
import shutil, time

ROOT = Path.home() / "companyos"
p = ROOT / "companyos/evolution/self_evolution_promotion_engine.py"
if not p.exists():
    raise SystemExit("FAIL: self_evolution_promotion_engine.py not found")

s = p.read_text(encoding="utf-8")
backup = p.with_name(p.name + ".bak.sandbox_import_fix." + str(int(time.time())))
shutil.copy2(p, backup)

start = s.find("def import_test(path: Path) -> dict:")
end = s.find("\ndef discover_tests_for(", start)
if start < 0 or end < 0:
    raise SystemExit("FAIL: import_test() block not found")

new = '''def import_test(path: Path) -> dict:
    code = f"""
import importlib.util, json, sys
from pathlib import Path
p = Path({str(path)!r}).resolve()
sys.path.insert(0, str(p.parent))
spec = importlib.util.spec_from_file_location("companyos_candidate_module", str(p))
if spec is None or spec.loader is None:
    raise RuntimeError("unable to create module spec")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print(json.dumps({{"ok": True, "module": getattr(m, "__name__", None)}}))
"""
    try:
        cp = subprocess.run(
            ["python", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TEST_TIMEOUT,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout": cp.stdout[-4000:],
            "stderr": cp.stderr[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("PROMOTION_ENGINE_SANDBOX_IMPORT_PATCH: PASS")
print("BACKUP:", backup)
