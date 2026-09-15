from companyos.runtime import autonomous_workforce_loop as m

class F:
    def __init__(self):
        self.reg={"workers":[
          {"status":"probation","id":"a"},
          {"status":"permanent","id":"b"},
          {"status":"retired","id":"c"}]}
    def active(self,t):
        return t.get("status") in ("probation","permanent")

def test_actual_factory_contract():
    f=F()
    assert len(m._workers(f))==3
    assert [x["id"] for x in m._active(f)]==["a","b"]

def test_active_is_called_with_worker():
    class X(F):
        def active(self,t):
            assert isinstance(t,dict)
            return super().active(t)
    assert len(m._active(X()))==2

def test_finance_not_implemented_here():
    src=(m.ROOT/"companyos/runtime/autonomous_workforce_loop.py").read_text()
    assert "SOLANA_PRIVATE_KEY" not in src
    assert "finance_ledger" not in src
