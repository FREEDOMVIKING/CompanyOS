from companyos.runtime.adaptive_worker_factory import ROLES,BOTTLENECKS
def test_coverage(): assert set(BOTTLENECKS)<=set(ROLES)
def test_bounded(): assert len(BOTTLENECKS)<=8
def test_unprivileged():
 s=" ".join(ROLES.values()).lower()
 assert all(x not in s for x in ("wallet","finance","credential","approval"))
