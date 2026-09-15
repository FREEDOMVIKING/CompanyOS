from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
def now():return datetime.now(timezone.utc).isoformat()
class VenturePerformanceFeedback:
    def __init__(self,root):self.root=Path(root);self.rt=self.root/".companyos_runtime"
    def run(self):
        p=self.rt/"post_launch_revenue_latest.json"
        if not p.exists():return {"status":"waiting","reason":"no_post_launch_result"}
        r=json.loads(p.read_text())
        signal={"timestamp":now(),"source":"venture_performance_feedback",
                "opportunity_id":r.get("opportunity_id"),"decision":r.get("decision"),
                "confidence":r.get("confidence"),"reason":r.get("reason"),
                "next_action":r.get("next_action"),"observed_revenue":r.get("evidence",{}).get("revenue"),
                "observed_conversions":r.get("evidence",{}).get("conversions")}
        q=self.rt/"profit_feedback_queue.jsonl"
        with q.open("a") as f:f.write(json.dumps(signal,sort_keys=True)+"\n")
        (self.rt/"venture_performance_feedback.json").write_text(json.dumps(signal,indent=2,sort_keys=True))
        return {"status":"queued","signal":signal}
