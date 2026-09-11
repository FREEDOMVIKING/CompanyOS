from companyos.providerexec import AdapterRegistry, HTTPProviderAdapter, ProviderApprovalGate

def test_registry():
    r=AdapterRegistry()
    r.register(HTTPProviderAdapter())
    assert r.get("http_generic") is not None

def test_simulated_http():
    assert HTTPProviderAdapter().execute({"url":"https://example.com"},live=False)["success"]

def test_gate():
    assert ProviderApprovalGate().evaluate({"kind":"bank_transfer","amount":1000})["requires_approval"]
