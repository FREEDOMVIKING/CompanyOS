import tempfile,time
from pathlib import Path
from companyos.runtime.durable_execution_kernel import DurableExecutionKernel
from companyos.runtime.lease_execution_guard import LeaseExecutionGuard
def test_success():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d)); g=LeaseExecutionGuard(k.db_path)
        ok,v,e=g.execute("v35a","w",lambda:7,ttl=2,interval=.1)
        assert ok and v==7 and e is None
def test_duplicate_blocked():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d)); g=LeaseExecutionGuard(k.db_path)
        x=g.store.claim("v35b","x",ttl=10); assert x
        ok,v,e=g.execute("v35b","w",lambda:7)
        assert not ok and e=="lease_unavailable"
        g.store.release(x)
def test_long_work_heartbeat():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d)); g=LeaseExecutionGuard(k.db_path)
        ok,v,e=g.execute("v35c","w",lambda:(time.sleep(1.3) or 9),ttl=1,interval=.2)
        assert ok and v==9
