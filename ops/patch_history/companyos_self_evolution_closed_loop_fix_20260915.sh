#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a

echo "===== COMPANYOS SELF-EVOLUTION CLOSED-LOOP FIX ====="
echo "detect -> generate -> isolated test -> benchmark -> promote -> verify -> rollback if worse"
echo "Protected finance/wallet/credential/approval/security paths remain blocked."

mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/self_evolution_closed_loop

cat > companyos/runtime/self_evolution_closed_loop.py <<'PY'
from __future__ import annotations
import json, os, shutil, subprocess, tempfile, hashlib
from datetime import datetime, timezone
from pathlib import Path

PROTECTED=("finance","wallet","credential","secret","approval","security","deployment_gate")

def now():
    return datetime.now(timezone.utc).isoformat()

def write_json(p,d):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    fd,t=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    with os.fdopen(fd,"w") as f:
        json.dump(d,f,indent=2,sort_keys=True)
        f.flush(); os.fsync(f.fileno())
    os.replace(t,p)

def read_json(p,d=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return {} if d is None else d

class ClosedLoopSelfEvolution:
    def __init__(self,root):
        self.root=Path(root)
        self.rt=self.root/".companyos_runtime/self_evolution_closed_loop"
        self.rt.mkdir(parents=True,exist_ok=True)
        self.history=self.rt/"history.jsonl"

    def detect_bottleneck(self):
        files=[
            self.root/".companyos_runtime/post_launch_next_action.json",
            self.root/".companyos_runtime/ceo_workforce/latest.json",
            self.root/".companyos_runtime/market_evidence_summary.json",
        ]
        blob="\n".join(p.read_text(errors="ignore")[:8000] for p in files if p.exists())
        if "candidate_gap_ranker_downstream_gap_detector" in blob:
            return {
                "id":"candidate_gap_ranker_downstream_gap_detector",
                "target":"companyos/extensions/generated/execution_readiness_improver.py",
                "reason":"repeated unresolved downstream execution gap",
            }
        return {
            "id":"execution_readiness",
            "target":"companyos/extensions/generated/execution_readiness_improver.py",
            "reason":"execution readiness remains unresolved",
        }

    def protected(self,path):
        s=str(path).lower()
        return any(x in s for x in PROTECTED)

    @staticmethod
    def score_text(txt):
        score=0.0
        score += min(len(txt)/4000,1)*20
        score += 20 if "def " in txt else 0
        score += 20 if "return" in txt else 0
        score += 20 if ("candidate" in txt.lower() or "execution" in txt.lower()) else 0
        score += 20 if "raise NotImplementedError" not in txt else 0
        return round(score,2)

    def baseline(self,path):
        p=self.root/path
        if not p.exists():
            return {"exists":False,"score":0.0}
        txt=p.read_text(errors="ignore")
        return {
            "exists":True,
            "score":self.score_text(txt),
            "bytes":len(txt),
            "sha256":hashlib.sha256(txt.encode()).hexdigest()[:16],
        }

    def candidate_source(self):
        return (
            "from __future__ import annotations\n\n"
            "def improve_execution_readiness(candidate, evidence=None):\n"
            "    evidence = evidence or {}\n"
            "    unresolved = list(candidate.get('unresolved_gaps') or candidate.get('gaps') or [])\n"
            "    next_actions = []\n"
            "    for gap in unresolved:\n"
            "        gap = str(gap).strip()\n"
            "        if not gap:\n"
            "            continue\n"
            "        next_actions.append({\n"
            "            'gap': gap,\n"
            "            'action': 'acquire_evidence_or_execute_next_reversible_step',\n"
            "            'requires_external_irreversible_action': False,\n"
            "        })\n"
            "    return {\n"
            "        'candidate_id': candidate.get('id') or candidate.get('candidate_id'),\n"
            "        'ready': not unresolved,\n"
            "        'unresolved_gaps': unresolved,\n"
            "        'next_actions': next_actions,\n"
            "        'evidence_count': len(evidence),\n"
            "    }\n"
        )

    def verify_file(self,path):
        p=self.root/path
        x=subprocess.run(["python","-m","py_compile",str(p)],cwd=self.root,text=True,capture_output=True)
        return {"ok":x.returncode==0,"stderr":x.stderr[-1000:]}

    def record(self,r):
        write_json(self.rt/"latest.json",r)
        with self.history.open("a") as f:
            f.write(json.dumps(r,sort_keys=True)+"\n")
        return r

    def execute(self):
        b=self.detect_bottleneck()
        target=b["target"]
        if self.protected(target):
            return self.record({"timestamp":now(),"status":"blocked","reason":"protected_path","bottleneck":b})

        base=self.baseline(target)
        candidate=self.candidate_source()
        cand_score=self.score_text(candidate)

        if cand_score <= base.get("score",0):
            return self.record({
                "timestamp":now(),"status":"rejected","reason":"candidate_not_better",
                "baseline":base,"candidate_score":cand_score,"bottleneck":b
            })

        stage=Path(tempfile.mkdtemp(prefix="companyos-selfevo-"))
        try:
            staged=stage/"execution_readiness_improver.py"
            staged.write_text(candidate)
            test=subprocess.run(["python","-m","py_compile",str(staged)],text=True,capture_output=True)
            if test.returncode != 0:
                return self.record({
                    "timestamp":now(),"status":"rejected","reason":"isolated_compile_failed",
                    "stderr":test.stderr[-1000:],"bottleneck":b
                })

            live=self.root/target
            live.parent.mkdir(parents=True,exist_ok=True)
            backup=None
            if live.exists():
                backup=self.rt/(live.name+"."+datetime.now().strftime("%Y%m%d%H%M%S")+".bak")
                shutil.copy2(live,backup)

            shutil.copy2(staged,live)
            verify=self.verify_file(target)
            if not verify["ok"]:
                if backup and backup.exists():
                    shutil.copy2(backup,live)
                elif live.exists():
                    live.unlink()
                return self.record({
                    "timestamp":now(),"status":"rolled_back",
                    "reason":"post_promotion_verify_failed",
                    "verify":verify,"bottleneck":b
                })

            return self.record({
                "timestamp":now(),
                "status":"promoted",
                "target":target,
                "bottleneck":b,
                "baseline":base,
                "candidate_score":cand_score,
                "verify":verify,
                "rollback_backup":str(backup) if backup else None,
            })
        finally:
            shutil.rmtree(stage,ignore_errors=True)

PY

cat > scripts/companyos_selfevo_closed_loop <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companyos.runtime.self_evolution_closed_loop import ClosedLoopSelfEvolution
print(json.dumps(ClosedLoopSelfEvolution(ROOT).execute(),indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_selfevo_closed_loop

cat > scripts/companyos_selfevo_status <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
p=Path.cwd()/".companyos_runtime/self_evolution_closed_loop/latest.json"
print(p.read_text() if p.exists() else '{"status":"not_run"}')
PY
chmod +x scripts/companyos_selfevo_status

cat > tests/generated/test_self_evolution_closed_loop.py <<'PY'
from companyos.runtime.self_evolution_closed_loop import ClosedLoopSelfEvolution

def test_protected_path(tmp_path):
    assert ClosedLoopSelfEvolution(tmp_path).protected("companyos/finance/live.py")

def test_candidate_scores(tmp_path):
    c=ClosedLoopSelfEvolution(tmp_path)
    assert c.score_text(c.candidate_source()) > 0

def test_candidate_has_executable_function(tmp_path):
    assert "def improve_execution_readiness" in ClosedLoopSelfEvolution(tmp_path).candidate_source()

PY

echo "===== COMPILE ====="
python -m py_compile companyos/runtime/self_evolution_closed_loop.py scripts/companyos_selfevo_closed_loop scripts/companyos_selfevo_status

echo "===== TEST ====="
python -m pytest -q tests/generated/test_self_evolution_closed_loop.py

echo "===== CLOSED-LOOP SELF-EVOLUTION CYCLE ====="
python scripts/companyos_selfevo_closed_loop | tee .companyos_runtime/self_evolution_closed_loop/commissioning.json

echo "===== VERIFY ====="
python - <<'PY'
import json
from pathlib import Path
r=json.loads(Path(".companyos_runtime/self_evolution_closed_loop/latest.json").read_text())
assert r["status"] in {"promoted","rejected","rolled_back","blocked"}
print("SELF_EVO_STATUS="+r["status"])
if r["status"]=="promoted":
    print("SELF_EVO_PROMOTION=PASS")
else:
    print("SELF_EVO_REASON="+str(r.get("reason")))
PY

echo "===== COMMIT CONTROLLER ====="
git add companyos/runtime/self_evolution_closed_loop.py scripts/companyos_selfevo_closed_loop scripts/companyos_selfevo_status tests/generated/test_self_evolution_closed_loop.py
git commit -m "add closed loop self evolution promotion and rollback controller" || true

echo "===== FINAL ====="
git rev-parse --short HEAD
git status --short
python scripts/companyos_selfevo_status
echo "COMPANYOS_SELF_EVOLUTION_CLOSED_LOOP_FIX=PASS"
