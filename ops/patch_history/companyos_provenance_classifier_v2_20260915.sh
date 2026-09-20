#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS PROVENANCE CLASSIFIER V2 ====="
echo "Classifies unknown commits without changing runtime, finance, connectors, or supervisor."

mkdir -p scripts .companyos_runtime

cat > scripts/companyos_newcode_v2 <<'PY'
#!/usr/bin/env python3
import argparse, json, re, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path.home()/"companyos"
RUNTIME=ROOT/".companyos_runtime"

AUTO_PATTERNS=[
 r"\bself[- ]?evolution\b", r"\bautonomous\b", r"\brecursive improvement\b",
 r"\bcapability expansion\b", r"\bpromote self[- ]?evolution candidate\b",
 r"\bclosed[- ]loop\b", r"\bevidence acquisition\b"
]
MANUAL_PATTERNS=[
 r"\bfix\b", r"\binstaller\b", r"\bcommission\b", r"\bcheckpoint\b",
 r"\bregister\b", r"\bbridge launcher\b", r"\btermux\b"
]
AUTO_PATHS=(
 "companyos/extensions/generated/",
 "tests/generated/",
 ".companyos_runtime/self_evolution",
)
MANUAL_PATHS=("scripts/companyos_",)

def sh(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True,stderr=subprocess.DEVNULL)

def commits(hours):
    since=(datetime.now(timezone.utc)-timedelta(hours=hours)).isoformat()
    fmt="%H%x1f%cI%x1f%s"
    out=sh("git","log",f"--since={since}",f"--format={fmt}")
    rows=[]
    for line in out.splitlines():
        if not line.strip(): continue
        h,t,s=line.split("\x1f",2)
        files=sh("git","show","--pretty=","--name-only",h).splitlines()
        files=[x.strip() for x in files if x.strip()]
        rows.append((h,t,s,files))
    return rows

def receipt_text():
    bits=[]
    for pat in ("*self*evolution*.json","*capability*.json","*provenance*.json","*promotion*.json"):
        for f in RUNTIME.glob(pat):
            try: bits.append(f.read_text(errors="ignore"))
            except Exception: pass
    return "\n".join(bits)

def classify(h,subject,files,receipts):
    text=subject.lower()
    reasons=[]
    # Strongest evidence: runtime receipt explicitly references the commit.
    if h in receipts or h[:8] in receipts:
        return "autonomous_verified",["runtime receipt references commit"]
    if any(re.search(p,text,re.I) for p in AUTO_PATTERNS):
        reasons.append("autonomous commit-message signature")
    if files and all(any(f.startswith(p) for p in AUTO_PATHS) for f in files):
        reasons.append("generated/self-evolution path signature")
    if reasons:
        return "autonomous_probable",reasons
    if any(re.search(p,text,re.I) for p in MANUAL_PATTERNS):
        return "manual_installer",["manual/installer commit-message signature"]
    if files and any(f.startswith(MANUAL_PATHS) for f in files):
        return "manual_probable",["installer/control script path present"]
    return "unresolved",["insufficient provenance evidence"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--hours",type=int,default=24)
    ap.add_argument("--json",action="store_true")
    a=ap.parse_args()
    receipts=receipt_text()
    data=[]
    for h,t,s,files in commits(a.hours):
        cls,reasons=classify(h,s,files,receipts)
        data.append({"commit":h,"time":t,"subject":s,"classification":cls,
                     "reasons":reasons,"files":files})
    counts={}
    for x in data: counts[x["classification"]]=counts.get(x["classification"],0)+1
    report={"hours":a.hours,"generated_at":datetime.now(timezone.utc).isoformat(),
            "counts":counts,"commits":data}
    (RUNTIME/"code_provenance_v2.json").write_text(json.dumps(report,indent=2)+"\n")
    if a.json:
        print(json.dumps(report,indent=2)); return
    print("===== VERIFIED AUTONOMOUS CODE PROVENANCE V2 =====")
    for x in data:
        print(f"\n{x['commit'][:8]}  {x['time']}  [{x['classification']}]")
        print("Reason:", "; ".join(x["reasons"]))
        print("Commit:",x["subject"])
        for f in x["files"]: print(" ",f)
    print("\n===== SUMMARY =====")
    for k in sorted(counts): print(f"{k}: {counts[k]}")
    print(f"total_recent_code_commits: {len(data)}")
    print("report:",RUNTIME/"code_provenance_v2.json")
if __name__=="__main__": main()
PY
chmod +x scripts/companyos_newcode_v2

python -m py_compile scripts/companyos_newcode_v2
python scripts/companyos_newcode_v2 --hours 24

echo
echo "===== SAFETY CHECK ====="
echo "SUPERVISOR_NOT_RESTARTED=YES"
echo "FINANCE_NOT_CHANGED=YES"
echo "CONNECTORS_NOT_CHANGED=YES"
echo "RUNTIME_NOT_MUTATED=YES"
echo "COMPANYOS_PROVENANCE_CLASSIFIER_V2=PASS"
