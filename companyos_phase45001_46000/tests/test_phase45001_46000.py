from companyos.walletsource import ProposalSourceInjector, ExecutionSourceGuard
IDENTITY={"success":True,"public_address":"ABC"}
def test_inject():
    assert ProposalSourceInjector().inject({}, IDENTITY)["proposal"]["source"]=="ABC"
def test_reject():
    assert ProposalSourceInjector().inject({"source":"XYZ"}, IDENTITY)["success"] is False
def test_guard():
    assert ExecutionSourceGuard().validate({"source":"ABC"}, IDENTITY)["allowed"] is True
