from pathlib import Path
import py_compile, json, tempfile

ROOT = Path.home()/"companyos"
files = [
    ROOT/"companyos/launch/autonomous_domain_web_launch.py",
    ROOT/"scripts/companyos_launch_venture.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.launch.autonomous_domain_web_launch import domain_candidates, generate_site
venture = {
    "name": "Verification Venture",
    "description": "Verification site",
    "launch_ready": True,
}
domains = domain_candidates(venture)
if not domains or not domains[0].endswith(".com"):
    raise SystemExit("VERIFY_FAIL: domain generation")
site = generate_site(venture)
if not (site/"index.html").exists():
    raise SystemExit("VERIFY_FAIL: site generation")

print("DOMAIN_CANDIDATE_GENERATION: PASS")
print("PRODUCTION_SITE_GENERATION: PASS")
print("AUTONOMOUS_DOMAIN_WEB_LAUNCH_ENGINE_VERIFY: PASS")
