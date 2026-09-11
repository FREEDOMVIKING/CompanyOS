from companyos.ceofinops import ExpectedValueEngine, CapitalAllocator

def test_positive_ev():
    e = ExpectedValueEngine().evaluate({
        "required_capital":10,
        "expected_return":30,
        "confidence":0.8,
        "risk":0.1
    })
    assert e["positive_ev"] is True

def test_reserve_protected():
    alloc = CapitalAllocator().allocate(
        [{
            "plan":{"required_capital":900},
            "evaluation":{"net_expected_value":100,"expected_gain":100,"positive_ev":True}
        }],
        available_capital=1000,
        reserve_floor=250
    )
    assert alloc["allocations"][0]["allocated_capital"] == 750
