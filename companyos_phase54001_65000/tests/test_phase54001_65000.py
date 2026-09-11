import os
from companyos.liveintegration import LiveExecutionPolicy, ReceiptReconciler

def test_policy_default_bounded():
    os.environ["COMPANYOS_LIVE_MAX_SINGLE"]="0.001"
    p=LiveExecutionPolicy()
    assert p.check_amount(0.1)["allowed"] is False

def test_receipt():
    r=ReceiptReconciler().reconcile({"signature":"x"},{"success":True})
    assert r["success"] is True
