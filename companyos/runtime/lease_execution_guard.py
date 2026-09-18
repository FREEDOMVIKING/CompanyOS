from __future__ import annotations
import json, os, threading, time
from pathlib import Path
from typing import Any, Callable
from companyos.runtime.worker_lease_store import WorkerLeaseStore

class LeaseExecutionGuard:
    def __init__(self, db_path: Path):
        self.store=WorkerLeaseStore(Path(db_path))
        self.cp=Path.home()/".companyos_runtime"/"execution_checkpoints"
        self.cp.mkdir(parents=True,exist_ok=True)
    def _write(self, tid, data):
        p=self.cp/f"{tid}.json"; t=p.with_suffix(".tmp")
        t.write_text(json.dumps(data,sort_keys=True)); os.replace(t,p)
    def execute(self, tid:str, owner:str, fn:Callable[[],Any], ttl:float=90, interval:float=20):
        lease=self.store.claim(tid,owner,ttl=ttl)
        if lease is None: return False,None,"lease_unavailable"
        stop=threading.Event(); lost=threading.Event()
        def hb():
            while not stop.wait(max(.25,interval)):
                try:
                    if not self.store.heartbeat(lease,ttl=ttl):
                        lost.set(); return
                except Exception:
                    lost.set(); return
        self._write(tid,{"state":"claimed","owner":owner,"token":lease.token,"time":time.time()})
        th=threading.Thread(target=hb,daemon=True); th.start()
        try:
            val=fn()
            if lost.is_set() or not self.store.heartbeat(lease,ttl=ttl):
                self._write(tid,{"state":"lease_lost","time":time.time()})
                return False,None,"lease_lost"
            self._write(tid,{"state":"completed","time":time.time()})
            return True,val,None
        except Exception as e:
            self._write(tid,{"state":"failed","error":f"{type(e).__name__}: {e}","time":time.time()})
            return False,None,f"{type(e).__name__}: {e}"
        finally:
            stop.set(); th.join(timeout=2); self.store.release(lease)
