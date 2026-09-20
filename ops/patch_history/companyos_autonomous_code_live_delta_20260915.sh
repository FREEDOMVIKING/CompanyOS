#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
mkdir -p scripts .companyos_runtime
cat > scripts/companyos_selfcode_live <<'PY'
#!/usr/bin/env python3
import json, subprocess, time, sys
from datetime import datetime
from pathlib import Path
ROOT=Path.home()/"companyos"; STATE=ROOT/".companyos_runtime/selfcode_live_seen.json"; REPORT=ROOT/".companyos_runtime/code_provenance_v2.json"
def refresh():
    subprocess.run([sys.executable,str(ROOT/"scripts/companyos_newcode_v2"),"--hours","24","--json"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def report():
    try:return json.loads(REPORT.read_text())
    except:return {"commits":[]}
def save(s):
    STATE.write_text(json.dumps({"seen":sorted(s),"updated_at":datetime.now().astimezone().isoformat()},indent=2)+"\n")
refresh(); r=report(); seen={x.get("commit") for x in r["commits"] if x.get("commit")}
save(seen)
print("===== COMPANYOS SELF-CREATED CODE — DELTA LIVE FEED =====")
print("Baseline captured:",datetime.now().astimezone().isoformat())
print("Existing commits hidden. Only NEW autonomous commits will appear.")
print("Refresh: 15 seconds | CTRL+C to exit")
try:
 while True:
    refresh()
    for c in reversed(report().get("commits",[])):
        h=c.get("commit")
        if not h or h in seen: continue
        if c.get("classification") in ("autonomous_verified","autonomous_probable"):
            print("\n"+"="*64)
            print("NEW SELF-CREATED CODE")
            print("time:",c.get("time")); print("commit:",h)
            print("classification:",c.get("classification"))
            print("reason:","; ".join(c.get("reasons",[])))
            print("description:",c.get("subject")); print("files:")
            for f in c.get("files",[]): print(" ",f)
            print("="*64,flush=True)
        seen.add(h)
    save(seen); print(".",end="",flush=True); time.sleep(15)
except KeyboardInterrupt:
 print("\nViewer stopped. CompanyOS runtime was not changed.")
PY
chmod +x scripts/companyos_selfcode_live
python -m py_compile scripts/companyos_selfcode_live
echo "DELTA_VIEWER_INSTALL=PASS"
echo "Supervisor/finance/connectors untouched."
exec python scripts/companyos_selfcode_live
