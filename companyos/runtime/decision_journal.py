from __future__ import annotations
import json,time
from pathlib import Path

class DecisionJournal:
    def __init__(self,path=None):
        self.path=path or (Path.home()/".companyos_runtime"/"decision_journal.jsonl")
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self,decision_type,source_id,decision,payload=None):
        row={"timestamp_unix":time.time(),"decision_type":decision_type,"source_id":source_id,"decision":decision,"payload":dict(payload or {})}
        with self.path.open("a") as f: f.write(json.dumps(row,sort_keys=True)+"\n")
        return row
