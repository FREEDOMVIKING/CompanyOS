from companyos.transactionops import TransactionPolicy, BalanceAndFeeGuard

def test_policy_limit():
    assert TransactionPolicy(1,0.1).validate(2,"A",{"A"})["allowed"] is False

def test_allowlist():
    assert TransactionPolicy(1,0.1).validate(0.5,"B",{"A"})["allowed"] is False

def test_reserve():
    assert BalanceAndFeeGuard().validate(1,0.5,0.1,0.5)["allowed"] is False
