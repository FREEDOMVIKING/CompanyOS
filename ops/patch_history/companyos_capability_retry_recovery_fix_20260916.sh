#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS CAPABILITY RETRY / JUNK-ID RECOVERY FIX ====="
echo "No supervisor restart. No finance/connectors changes."

ts="$(date +%Y%m%d_%H%M%S)"
mkdir -p ".companyos_backups/$ts"
cp companyos/runtime/capability_expansion.py ".companyos_backups/$ts/capability_expansion.py"
cp companyos/runtime/capability_request_executor.py ".companyos_backups/$ts/capability_request_executor.py"

python - <<'PY'
from pathlib import Path

p = Path("companyos/runtime/capability_expansion.py")
s = p.read_text()

old = '''def canonical_paths(capability_id):
 cid=re.sub(r"[^a-zA-Z0-9_]+","_",str(capability_id or "")).strip("_").lower()
 if not cid: raise ValueError("missing capability id")
 return (
  f"companyos/extensions/generated/{cid}.py",
  f"tests/generated/test_{cid}.py",
 )
'''
new = '''JUNK_CAPABILITY_IDS={
 "x","xx","xxx","test","tmp","temp","foo","bar","baz","demo","sample",
 "capability","new_capability","unknown","none","null","todo","fix","helper"
}

def normalize_capability_id(capability_id):
 cid=re.sub(r"[^a-zA-Z0-9_]+","_",str(capability_id or "")).strip("_").lower()
 if not cid:
  raise ValueError("missing_capability_id")
 if cid in JUNK_CAPABILITY_IDS:
  raise ValueError("junk_capability_id:"+cid)
 if len(cid) < 4:
  raise ValueError("capability_id_too_short:"+cid)
 if cid.isdigit():
  raise ValueError("numeric_capability_id:"+cid)
 if not re.search(r"[a-z]",cid):
  raise ValueError("capability_id_missing_letters:"+cid)
 return cid

def canonical_paths(capability_id):
 cid=normalize_capability_id(capability_id)
 return (
  f"companyos/extensions/generated/{cid}.py",
  f"tests/generated/test_{cid}.py",
 )
'''
if old not in s:
    raise SystemExit("capability_expansion canonical_paths anchor not found")
s = s.replace(old, new, 1)
p.write_text(s)

p = Path("companyos/runtime/capability_request_executor.py")
s = p.read_text()

anchor = '''def _gap(req):
    cid=str(req["requested_capability"])
    return {"id":cid,"title":cid.replace("_"," ").title(),"reason":str(req.get("reason") or "Compounding capability request"),"source_capability":req.get("source_capability"),"gap_type":req.get("gap_type"),"gap_id":req.get("gap_id")}
'''
insert = '''def _replacement_capability_id(req):
    text=" ".join(str(req.get(k) or "") for k in ("gap_type","reason","requested_capability","gap_id")).lower()
    mapping=(
        (("missing_executable_next_action","executable next action"),"executable_next_action_planner"),
        (("missing_external_evidence","external evidence"),"external_evidence_requirements_analyzer"),
        (("profit_unestimated","profit unestimated","profitability"),"profitability_estimator"),
        (("probability_unestimated","probability unestimated"),"probability_estimator"),
        (("missing_revenue_evidence","revenue evidence"),"revenue_evidence_analyzer"),
        (("qualification","candidate gap","execution-qualified"),"candidate_gap_ranker"),
    )
    for needles,cid in mapping:
        if any(n in text for n in needles):
            return cid
    return "semantic_gap_resolution_analyzer"

def _gap(req):
    cid=str(req["requested_capability"])
    return {"id":cid,"title":cid.replace("_"," ").title(),"reason":str(req.get("reason") or "Compounding capability request"),"source_capability":req.get("source_capability"),"gap_type":req.get("gap_type"),"gap_id":req.get("gap_id")}

def _retry_or_reject(queue,index,req,result,**details):
    attempts=int(req.get("generation_retry_count") or 0)+1
    max_attempts=max(1,int(os.getenv("COMPANYOS_CAPABILITY_GENERATION_MAX_RETRIES","3")))
    updates=dict(details)
    updates["result"]=result
    updates["generation_retry_count"]=attempts
    updates["last_attempt"]=result
    if attempts < max_attempts:
        updates["status"]="research_required"
        updates["retry_after_unix"]=time.time()
        updates["retry_reason"]="candidate_generation_or_validation_failed"
        emit("capability_retry_queued",
             capability=req.get("requested_capability"),
             gap_id=req.get("gap_id"),
             attempt=attempts,
             reason=result)
        _update(queue,index,**updates)
        return {"ok":True,"status":"retry_queued","reason":result,"attempt":attempts}
    updates["status"]="rejected_terminal"
    updates["rejected_at"]=time.time()
    emit("capability_retry_exhausted",
         capability=req.get("requested_capability"),
         gap_id=req.get("gap_id"),
         attempts=attempts,
         reason=result)
    _update(queue,index,**updates)
    return {"ok":False,"status":"retry_exhausted","reason":result,"attempts":attempts}
'''
if anchor not in s:
    raise SystemExit("request_executor _gap anchor not found")
s = s.replace(anchor, insert, 1)

old = '''    i,req=selected
    gap=_gap(req); cid=gap["id"]
    inv=ce.capability_inventory()
'''
new = '''    i,req=selected

    original_cid=str(req.get("requested_capability") or "")
    try:
        ce.canonical_paths(original_cid)
    except Exception as exc:
        replacement=_replacement_capability_id(req)
        try:
            ce.canonical_paths(replacement)
        except Exception:
            replacement="semantic_gap_resolution_analyzer"
        queue=load(QUEUE,{"requests":[]})
        _update(queue,i,
                status="research_required",
                requested_capability=replacement,
                recovered_from_capability_id=original_cid,
                recovery_reason="invalid_or_junk_capability_id",
                recovery_error=repr(exc),
                recovered_at=time.time())
        emit("junk_capability_id_recovered",
             original=original_cid,
             replacement=replacement,
             gap_id=req.get("gap_id"))
        queue=load(QUEUE,{"requests":[]})
        req=queue["requests"][i]

    gap=_gap(req); cid=gap["id"]
    inv=ce.capability_inventory()
'''
if old not in s:
    raise SystemExit("request_executor selected anchor not found")
s = s.replace(old, new, 1)

pairs = [
('''        except Exception as exc:
            _update(queue,i,status="rejected",result="existing_capability_failed",error=repr(exc))
            return {"ok":False,"status":"existing_capability_failed","error":repr(exc)}
''',
'''        except Exception as exc:
            queue=load(QUEUE,{"requests":[]})
            return _retry_or_reject(queue,i,req,"existing_capability_failed",error=repr(exc))
'''),
('''    if shape:
        queue=load(QUEUE,{"requests":[]})
        _update(queue,i,status="rejected",result="generation_shape_invalid",errors=shape)
        return {"ok":True,"status":"generation_shape_invalid","errors":shape}
''',
'''    if shape:
        queue=load(QUEUE,{"requests":[]})
        return _retry_or_reject(queue,i,req,"generation_shape_invalid",errors=shape)
'''),
('''    if errors:
        _update(queue,i,status="rejected",result="validation_failed",candidate_id=candidate_id,errors=errors)
        return {"ok":True,"status":"validation_rejected","errors":errors}
''',
'''    if errors:
        return _retry_or_reject(queue,i,req,"validation_failed",
                                candidate_id=candidate_id,errors=errors)
'''),
('''    if not ok:
        _update(queue,i,status="rejected",result="tests_failed",candidate_id=candidate_id,tests=tests)
        return {"ok":True,"status":"tests_rejected","tests":tests}
''',
'''    if not ok:
        return _retry_or_reject(queue,i,req,"tests_failed",
                                candidate_id=candidate_id,tests=tests)
'''),
('''    except Exception as exc:
        ce.rollback(cid)
        queue=load(QUEUE,{"requests":[]})
        _update(queue,i,status="rejected",result="canary_failed_rolled_back",candidate_id=candidate_id,error=repr(exc))
        return {"ok":False,"status":"canary_failed_rolled_back","error":repr(exc)}
''',
'''    except Exception as exc:
        ce.rollback(cid)
        queue=load(QUEUE,{"requests":[]})
        return _retry_or_reject(queue,i,req,"canary_failed_rolled_back",
                                candidate_id=candidate_id,error=repr(exc))
'''),
('''    if not gen.get("ok"):
        _update(queue,i,status="research_required",last_attempt="generation_failed",generation=gen)
        emit("generation_failed",capability=cid,gap_id=req.get("gap_id"))
        return {"ok":False,"status":"generation_failed","generation":gen}
''',
'''    if not gen.get("ok"):
        return _retry_or_reject(queue,i,req,"generation_failed",generation=gen)
''')
]
for a,b in pairs:
    if a not in s:
        raise SystemExit("request_executor patch anchor missing")
    s = s.replace(a,b,1)

p.write_text(s)
PY

echo "===== COMPILE ====="
python -m py_compile   companyos/runtime/capability_expansion.py   companyos/runtime/capability_request_executor.py

echo "===== REGRESSION TESTS ====="
mkdir -p tests/generated
cat > tests/generated/test_capability_junk_id_recovery_v1.py <<'PY'
import pytest
from companyos.runtime import capability_expansion as ce
from companyos.runtime import capability_request_executor as cre

def test_junk_ids_rejected():
    for cid in ("x","xx","test","tmp","foo","123"):
        with pytest.raises(ValueError):
            ce.canonical_paths(cid)

def test_meaningful_id_allowed():
    mod,test=ce.canonical_paths("executable_next_action_planner")
    assert mod.endswith("executable_next_action_planner.py")
    assert test.endswith("test_executable_next_action_planner.py")

def test_semantic_replacements():
    assert cre._replacement_capability_id(
        {"gap_type":"missing_executable_next_action"}
    ) == "executable_next_action_planner"
    assert cre._replacement_capability_id(
        {"reason":"candidate is missing external evidence"}
    ) == "external_evidence_requirements_analyzer"
    assert cre._replacement_capability_id(
        {"reason":"profit unestimated"}
    ) == "profitability_estimator"
PY

python -m pytest -q   tests/generated/test_capability_junk_id_recovery_v1.py   tests/generated/test_stale_completed_request_retrigger_v1.py

echo "===== SAFE ONE-SHOT EXECUTOR ====="
python -m companyos.runtime.capability_request_executor once || true

echo "===== SUPERVISOR PRESERVATION CHECK ====="
ps -ef | grep 'companyos/runtime/service_supervisor.py' | grep -v grep || true

git add   companyos/runtime/capability_expansion.py   companyos/runtime/capability_request_executor.py   tests/generated/test_capability_junk_id_recovery_v1.py

git commit -m "Recover junk capability IDs and retry failed generations safely" || true
git push origin "$(git branch --show-current)"

echo
echo "COMPANYOS_CAPABILITY_RETRY_RECOVERY_FIX=PASS"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CHANGED=NO"
echo "CONNECTORS_CHANGED=NO"
