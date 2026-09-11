from companyos.moneyops import FinancialKillSwitch, IdempotencyStore, MoneyOpsStatus
import tempfile
from pathlib import Path

def test_kill_switch():
    root = Path(tempfile.mkdtemp())
    k = FinancialKillSwitch(root)
    k.engage("x")
    assert k.engaged() is True
    k.clear()
    assert k.engaged() is False

def test_idempotency():
    root = Path(tempfile.mkdtemp())
    s = IdempotencyStore(root)
    s.put("k", {"v":1})
    assert s.get("k")["v"] == 1

def test_safe_default():
    assert MoneyOpsStatus().status()["live_execution_default"] is False
