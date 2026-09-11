from pathlib import Path
import py_compile
R=Path.home()/"companyos"
for x in ["companyos/governance/venture_lifecycle_progression.py","dashboard/lifecycle_progress_server.py","dashboard/lifecycle_progress.html","dashboard/lifecycle_progress_start.sh"]:
 p=R/x;print(x,"=>","PASS" if p.exists() else "FAIL")
 if not p.exists():raise SystemExit(1)
py_compile.compile(str(R/"companyos/governance/venture_lifecycle_progression.py"),doraise=True)
py_compile.compile(str(R/"dashboard/lifecycle_progress_server.py"),doraise=True)
print("LIFECYCLE_PROGRESSION_VERIFY: PASS")
