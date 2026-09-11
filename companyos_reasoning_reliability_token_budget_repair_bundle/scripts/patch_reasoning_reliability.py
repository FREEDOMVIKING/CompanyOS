from pathlib import Path
import shutil, time

ROOT = Path.home() / "companyos"

targets = [
    ROOT / "companyos" / "runtime" / "productive_autonomy_watchdog.py",
    ROOT / "companyos" / "runtime" / "autonomous_ceo_orchestrator.py",
]

snippet = """# COMPANYOS_REASONING_RELIABILITY_V1
try:
    from companyos.runtime.reasoning_reliability import install as _install_reasoning_reliability
    _install_reasoning_reliability()
except Exception:
    pass
"""

patched = []
for p in targets:
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8")
    if "COMPANYOS_REASONING_RELIABILITY_V1" in s:
        patched.append(str(p))
        continue
    backup = p.with_name(p.name + ".bak.reasoning_reliability." + str(int(time.time())))
    shutil.copy2(p, backup)

    lines = s.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from __future__ import"):
            insert_at = i + 1
    lines.insert(insert_at, snippet.rstrip())
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    patched.append(str(p))

if not patched:
    raise SystemExit("FAIL: no runtime entrypoints patched")

print("REASONING_RELIABILITY_PATCH: PASS")
for p in patched:
    print("PATCHED:", p)
