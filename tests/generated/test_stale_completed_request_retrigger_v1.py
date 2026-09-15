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
