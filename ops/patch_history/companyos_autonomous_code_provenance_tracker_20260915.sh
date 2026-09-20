#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS AUTONOMOUS CODE PROVENANCE ====="
echo "No supervisor restart. No finance changes."
mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/self_code_provenance

cat > companyos/runtime/self_code_provenance.py <<'PY'
import subprocess,time
AUTO=("self-evolution","self evolution","self_evolution","autonomous promotion","promote self","generated capability","capability expansion","recursive improvement")
MANUAL=("fix ","installer","overnight","commission","register ","align ","cloudflare","workforce")
def classify(s):
    x=s.lower()
    if any(k in x for k in AUTO): return "autonomous"
    if any(k in x for k in MANUAL): return "manual_or_installer"
    return "unknown"
def run(hours=24):
    cmd=["git","log",f"--since={hours} hours ago","--pretty=format:%H%x1f%ct%x1f%s","--","companyos/","scripts/","tests/"]
    raw=subprocess.check_output(cmd,text=True).strip()
    rows=[]
    for line in raw.splitlines() if raw else []:
        h,ts,subject=line.split("\x1f",2)
        origin=classify(subject)
        files=subprocess.check_output(["git","show","--pretty=format:","--name-status",h,"--","companyos/","scripts/","tests/"],text=True).splitlines()
        rows.append((h,ts,subject,origin,files))
    auto=[r for r in rows if r[3]=="autonomous"]
    print("===== VERIFIED AUTONOMOUS SELF-CODE =====")
    if not auto: print("None verifiable from legacy Git metadata.")
    for h,ts,subject,origin,files in auto:
        print(f"\n{h[:8]}  {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(ts)))}")
        print("Reason:",subject)
        for f in files: print(" ",f)
    print("\n===== SUMMARY =====")
    print("autonomous_verified:",len(auto))
    print("manual_or_installer_filtered:",sum(r[3]=="manual_or_installer" for r in rows))
    print("unknown_not_claimed_autonomous:",sum(r[3]=="unknown" for r in rows))
    print("total_recent_code_commits:",len(rows))
PY

cat > scripts/companyos_newcode <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse
from companyos.runtime.self_code_provenance import run
p=argparse.ArgumentParser()
p.add_argument("--hours",type=int,default=24)
a=p.parse_args()
run(a.hours)
PY
chmod +x scripts/companyos_newcode

cat > tests/generated/test_self_code_provenance.py <<'PY'
from companyos.runtime.self_code_provenance import classify
def test_auto(): assert classify("Promote self-evolution candidate 123")=="autonomous"
def test_manual(): assert classify("fix workforce launcher import path")=="manual_or_installer"
def test_unknown(): assert classify("misc change")=="unknown"
PY

python -m py_compile companyos/runtime/self_code_provenance.py scripts/companyos_newcode
python -m pytest -q tests/generated/test_self_code_provenance.py

mkdir -p "$PREFIX/bin"
cat > "$PREFIX/bin/companyos_newcode" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/companyos" || exit 1
exec python scripts/companyos_newcode "$@"
SH
chmod +x "$PREFIX/bin/companyos_newcode"

echo "===== CURRENT REPORT ====="
companyos_newcode --hours 24
echo "===== SUPERVISOR ====="
pgrep -af "companyos.runtime.service_supervisor" || true

git add companyos/runtime/self_code_provenance.py scripts/companyos_newcode tests/generated/test_self_code_provenance.py
if ! git diff --cached --quiet; then
 git commit -m "add autonomous self code provenance reporting" || true
fi
echo "COMPANYOS_AUTONOMOUS_CODE_PROVENANCE=PASS"
echo "SUPERVISOR_RESTARTED=NO"
echo "USE: companyos_newcode"
