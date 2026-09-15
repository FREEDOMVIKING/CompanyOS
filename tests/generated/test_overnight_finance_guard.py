from companyos.runtime.overnight_finance_guard import OvernightFinanceGuard
def test_aggregate_cap(tmp_path):
 g=OvernightFinanceGuard(tmp_path)
 assert g.reserve(30,"a")["allowed"];g.settle(30,"a",True)
 assert g.reserve(20,"b")["allowed"];g.settle(20,"b",True)
 assert not g.reserve(.01,"c")["allowed"]
 assert g.status()["spent_usd"]==50
def test_parallel_reservations_cannot_exceed_cap(tmp_path):
 import concurrent.futures
 g=OvernightFinanceGuard(tmp_path)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as x:
  rs=list(x.map(lambda i:g.reserve(10,f"t{i}"),range(8)))
 assert sum(bool(r["allowed"]) for r in rs)==5
 assert g.status()["reserved_usd"]==50
def test_failed_transaction_releases_budget(tmp_path):
 g=OvernightFinanceGuard(tmp_path);assert g.reserve(50,"x")["allowed"]
 g.settle(50,"x",False);assert g.status()["remaining_usd"]==50
def test_receiving_not_capped(tmp_path):
 g=OvernightFinanceGuard(tmp_path)
 assert g.receive(1000000,"USDC")["accepted"]
 assert g.status()["remaining_usd"]==50
