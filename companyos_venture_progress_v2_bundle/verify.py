from pathlib import Path
import py_compile

ROOT=Path.home()/"companyos"
files=[
 ROOT/"dashboard"/"venture_progress_v2_server.py",
 ROOT/"dashboard"/"venture_progress_v2.html",
 ROOT/"dashboard"/"venture_progress_v2_start.sh",
]
for p in files:
    print(p,"=>","PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
py_compile.compile(str(ROOT/"dashboard"/"venture_progress_v2_server.py"),doraise=True)
print("VENTURE_PROGRESS_V2_VERIFY: PASS")
