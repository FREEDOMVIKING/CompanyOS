#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== CompanyOS stale completed-request retrigger fix ====="

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/capability_request_executor.py")
s=p.read_text()
anchor='def process_one():\n    from companyos.runtime import capability_expansion as ce\n    queue=load(QUEUE,{"requests":[]})\n'
insert='''def _context_fingerprint(req):
    import hashlib
    ctx=_context(req)
    cr=ctx.get("compounding_request")
    if isinstance(cr,dict):
        cr=dict(cr)
        for k in ("status","updated_at","started_at","completed_at","last_attempt","generation","execution","promotion","result","error","candidate_id","retriggered_at","last_context_fingerprint"):
            cr.pop(k,None)
        ctx["compounding_request"]=cr
    raw=json.dumps(ctx,sort_keys=True,default=str,separators=(",",":"))
    return hashlib.sha256(raw.encode()).hexdigest()

def _retrigger_stale_completed(queue):
    now=time.time()
    reopened=0
    baseline_changed=False
    for req in queue.get("requests",[]):
        if not isinstance(req,dict) or req.get("status")!="completed" or not req.get("requested_capability"):
            continue
        fp=_context_fingerprint(req)
        previous=req.get("last_context_fingerprint")
        if not previous:
            req["last_context_fingerprint"]=fp
            baseline_changed=True
            continue
        if previous==fp:
            continue
        req["status"]="research_required"
        req["retriggered_at"]=now
        req["retrigger_reason"]="runtime_evidence_changed"
        req["last_context_fingerprint"]=fp
        reopened+=1
        emit("completed_request_retriggered",capability=req.get("requested_capability"),gap_id=req.get("gap_id"))
    if reopened or baseline_changed:
        atomic(QUEUE,queue)
    return reopened

def process_one():
    from companyos.runtime import capability_expansion as ce
    queue=load(QUEUE,{"requests":[]})
    _retrigger_stale_completed(queue)
    queue=load(QUEUE,{"requests":[]})
'''
if anchor not in s:
    raise SystemExit("PATCH_ANCHOR_NOT_FOUND")
s=s.replace(anchor,insert,1)
s=s.replace('_update(queue,i,status="completed",result="existing_capability_used",execution=execution,completed_at=time.time())',
'_update(queue,i,status="completed",result="existing_capability_used",execution=execution,completed_at=time.time(),last_context_fingerprint=_context_fingerprint(req))')
s=s.replace('_update(queue,i,status="completed",result="capability_promoted_and_used",candidate_id=candidate_id,promotion=receipt,execution=execution,completed_at=time.time())',
'_update(queue,i,status="completed",result="capability_promoted_and_used",candidate_id=candidate_id,promotion=receipt,execution=execution,completed_at=time.time(),last_context_fingerprint=_context_fingerprint(req))')
p.write_text(s)
PY

mkdir -p tests/generated
cat > tests/generated/test_stale_completed_request_retrigger_v1.py <<'PY'
import json, tempfile
from pathlib import Path
import companyos.runtime.capability_request_executor as m

def test_retrigger_only_when_context_changes():
    with tempfile.TemporaryDirectory() as td:
        oldq,oldctx=m.QUEUE,m._context
        try:
            m.QUEUE=Path(td)/"q.json"
            m.QUEUE.write_text(json.dumps({"requests":[{"status":"completed","requested_capability":"x","gap_id":"g"}]}))
            m._context=lambda r: {"evidence":{"v":1},"compounding_request":r}
            q=json.loads(m.QUEUE.read_text())
            assert m._retrigger_stale_completed(q)==0
            q=json.loads(m.QUEUE.read_text())
            assert q["requests"][0]["status"]=="completed"
            assert q["requests"][0].get("last_context_fingerprint")
            assert m._retrigger_stale_completed(q)==0
            m._context=lambda r: {"evidence":{"v":2},"compounding_request":r}
            q=json.loads(m.QUEUE.read_text())
            assert m._retrigger_stale_completed(q)==1
            q=json.loads(m.QUEUE.read_text())
            assert q["requests"][0]["status"]=="research_required"
            assert q["requests"][0]["retrigger_reason"]=="runtime_evidence_changed"
        finally:
            m.QUEUE,m._context=oldq,oldctx
PY

python -m py_compile companyos/runtime/capability_request_executor.py
python -m pytest -q tests/generated/test_stale_completed_request_retrigger_v1.py

echo "===== safe live cycle ====="
python -m companyos.runtime.capability_request_executor once || true

git add companyos/runtime/capability_request_executor.py tests/generated/test_stale_completed_request_retrigger_v1.py
git commit -m "Retrigger completed capabilities when runtime evidence changes" || true
git push origin "$(git branch --show-current)"

echo "STALE_COMPLETED_RETRIGGER_FIX=PASS"
echo "Supervisor was not restarted."
