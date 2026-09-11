from pathlib import Path
import shutil, time

ROOT = Path.home() / "companyos"
p = ROOT / "companyos/evolution/self_evolution_generator.py"
if not p.exists():
    raise SystemExit("FAIL: self_evolution_generator.py not found")

s = p.read_text(encoding="utf-8")
backup = p.with_name(p.name + ".bak.test_import_fix." + str(int(time.time())))
shutil.copy2(p, backup)

start = s.find("def tests_for(name: str) -> str:")
end = s.find("\ndef generate_one(", start)
if start < 0 or end < 0:
    raise SystemExit("FAIL: tests_for() block not found")

new = '''def tests_for(name: str) -> str:
    return f"""
from __future__ import annotations
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("{name}.py")
SPEC = importlib.util.spec_from_file_location("{name}", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

def test_generated_module_loads():
    assert MODULE is not None
""".strip() + "\\n"
'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("GENERATOR_SELF_CONTAINED_TEST_IMPORT_PATCH: PASS")
print("BACKUP:", backup)
