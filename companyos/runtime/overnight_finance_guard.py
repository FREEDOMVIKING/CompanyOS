from __future__ import annotations
import fcntl,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path

CAP=50.0
def now():return datetime.now(timezone.utc).isoformat()
class OvernightFinanceGuard:
    """Atomic aggregate outbound budget guard. Receiving is not charged."""
    def __init__(self,root):
        self.root=Path(root);self.d=self.root/".companyos_runtime/overnight"
        self.d.mkdir(parents=True,exist_ok=True);self.state=self.d/"finance_budget.json";self.lock=self.d/"finance_budget.lock"
        if not self.state.exists():self._write({"cap_usd":CAP,"spent_usd":0.0,"reserved_usd":0.0,"started_at":now(),"mode":"overnight"})
    def _read(self):
        try:return json.loads(self.state.read_text())
        except:return {"cap_usd":CAP,"spent_usd":0.0,"reserved_usd":0.0}
    def _write(self,d):
        fd,t=tempfile.mkstemp(dir=str(self.d),prefix="budget.")
        with os.fdopen(fd,"w") as f:json.dump(d,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(t,self.state)
    def reserve(self,usd,tx_id):
        usd=float(usd)
        if usd < 0:return {"allowed":False,"reason":"negative_amount"}
        with self.lock.open("a+") as lk:
            fcntl.flock(lk,fcntl.LOCK_EX);s=self._read()
            remaining=s["cap_usd"]-s["spent_usd"]-s["reserved_usd"]
            if usd > remaining+1e-9:return {"allowed":False,"reason":"overnight_cap_exceeded","remaining_usd":round(remaining,2)}
            s["reserved_usd"]=round(s["reserved_usd"]+usd,8);self._write(s)
            self._ledger({"kind":"reserve","tx_id":tx_id,"usd":usd,"timestamp":now()})
            return {"allowed":True,"remaining_after_reservation_usd":round(remaining-usd,2)}
    def settle(self,usd,tx_id,success):
        usd=float(usd)
        with self.lock.open("a+") as lk:
            fcntl.flock(lk,fcntl.LOCK_EX);s=self._read()
            s["reserved_usd"]=max(0,round(s["reserved_usd"]-usd,8))
            if success:s["spent_usd"]=round(s["spent_usd"]+usd,8)
            self._write(s);self._ledger({"kind":"settle","tx_id":tx_id,"usd":usd,"success":bool(success),"timestamp":now()})
            return s
    def receive(self,amount,asset,ref=None):
        # No inbound ceiling; this records evidence only and never signs a transfer.
        x={"kind":"receive","amount":amount,"asset":asset,"ref":ref,"timestamp":now()}
        self._ledger(x);return {"accepted":True,"counts_against_outbound_cap":False}
    def status(self):
        s=self._read();s["remaining_usd"]=round(s["cap_usd"]-s["spent_usd"]-s["reserved_usd"],2);return s
    def _ledger(self,x):
        with (self.d/"finance_ledger.jsonl").open("a") as f:f.write(json.dumps(x,sort_keys=True)+"\n")
