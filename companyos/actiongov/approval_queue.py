import json, uuid
from pathlib import Path
from datetime import datetime, timezone

class PersistentApprovalQueue:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"approval_queue.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return []
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,list) else []
        except Exception:return []

    def save(self, rows):
        self.path.write_text(json.dumps(rows,indent=2,default=str),encoding="utf-8")

    def submit(self, action):
        rows=self.load()
        row={
            "approval_id":"apr_"+uuid.uuid4().hex[:12],
            "action":action,
            "status":"pending",
            "created_at":datetime.now(timezone.utc).isoformat()
        }
        rows.append(row); self.save(rows); return row

    def decide(self, approval_id, decision, actor="human"):
        rows=self.load()
        updated=None
        for r in rows:
            if r.get("approval_id")==approval_id:
                r["status"]="approved" if decision=="approve" else "denied"
                r["decided_by"]=actor
                r["decided_at"]=datetime.now(timezone.utc).isoformat()
                updated=dict(r)
        self.save(rows)
        return updated

    def pending(self):
        return [r for r in self.load() if r.get("status")=="pending"]
