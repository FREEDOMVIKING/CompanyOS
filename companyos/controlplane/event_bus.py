import json, uuid
from pathlib import Path
from datetime import datetime, timezone

class EventBus:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"control_event_bus.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def _load(self):
        if not self.path.exists(): return []
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,list) else []
        except Exception:return []

    def _save(self, rows):
        self.path.write_text(json.dumps(rows,indent=2,default=str),encoding="utf-8")

    def publish(self, topic, payload=None, priority=5):
        rows=self._load()
        row={"event_id":"evt_"+uuid.uuid4().hex[:12],"topic":topic,"payload":payload or {},
             "priority":int(priority),"status":"pending",
             "timestamp":datetime.now(timezone.utc).isoformat()}
        rows.append(row); self._save(rows); return row

    def next(self, topics=None):
        rows=self._load()
        pending=[r for r in rows if r.get("status")=="pending" and (not topics or r.get("topic") in topics)]
        if not pending:return None
        pending.sort(key=lambda r:(-int(r.get("priority",0)),r.get("timestamp","")))
        chosen=pending[0]
        for r in rows:
            if r.get("event_id")==chosen.get("event_id"):
                r["status"]="processing"; chosen=dict(r); break
        self._save(rows); return chosen

    def ack(self,event_id):
        rows=self._load()
        for r in rows:
            if r.get("event_id")==event_id:r["status"]="complete"
        self._save(rows)

    def snapshot(self):
        rows=self._load()
        return {"total":len(rows),
                "pending":sum(1 for r in rows if r.get("status")=="pending"),
                "processing":sum(1 for r in rows if r.get("status")=="processing"),
                "complete":sum(1 for r in rows if r.get("status")=="complete")}
