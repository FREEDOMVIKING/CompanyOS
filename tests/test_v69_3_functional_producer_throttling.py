from companyos.runtime.productive_autonomy_watchdog import _producer_throttle_gate


def decisions(divisor: int, ticks: int, queued: int = 100):
    ws={}
    out=[]
    for _ in range(ticks):
        out.append(_producer_throttle_gate(
            {"snapshot":{"queued":queued},"producer_divisor":divisor},
            ws,
        ))
    return out


def test_divisor_1_allows_every_tick():
    rows=decisions(1,8)
    assert sum(x["allow_producer"] for x in rows)==8
    assert all(x["action"]=="producer_allowed" for x in rows)


def test_divisor_2_allows_one_of_two_ticks():
    rows=decisions(2,8)
    assert [x["allow_producer"] for x in rows] == [True,False,True,False,True,False,True,False]
    assert sum(x["allow_producer"] for x in rows)==4


def test_divisor_3_allows_one_of_three_ticks():
    rows=decisions(3,12)
    assert sum(x["allow_producer"] for x in rows)==4
    assert [i+1 for i,x in enumerate(rows) if x["allow_producer"]] == [1,4,7,10]


def test_divisor_4_allows_one_of_four_ticks():
    rows=decisions(4,12)
    assert sum(x["allow_producer"] for x in rows)==3
    assert [i+1 for i,x in enumerate(rows) if x["allow_producer"]] == [1,5,9]


def test_existing_hard_queue_stop_is_preserved(monkeypatch):
    monkeypatch.setenv("COMPANYOS_BACKPRESSURE_QUEUE_THRESHOLD","300")
    rows=decisions(1,4,queued=300)
    assert not any(x["allow_producer"] for x in rows)
    assert all(x["action"]=="backpressure_execution_first" for x in rows)


def test_growth_or_prethreshold_divisor_can_throttle_before_hard_stop(monkeypatch):
    monkeypatch.setenv("COMPANYOS_BACKPRESSURE_QUEUE_THRESHOLD","300")
    rows=decisions(3,6,queued=100)
    assert [x["allow_producer"] for x in rows] == [True,False,False,True,False,False]
    assert all(x["queued"]==100 for x in rows)
