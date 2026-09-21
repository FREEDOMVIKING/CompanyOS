import time
from companyos.runtime import openai_web_evidence_fallback as ow

def test_model_order_is_cost_aware_by_default(monkeypatch):
    monkeypatch.setattr(ow,"MODEL","gpt-5.6-luna")
    monkeypatch.setattr(
        ow,
        "MODEL_CANDIDATES",
        ("gpt-5.6-luna","gpt-5.6-terra","gpt-5.6-sol"),
    )
    assert ow._ordered_models()==[
        "gpt-5.6-luna",
        "gpt-5.6-terra",
        "gpt-5.6-sol",
    ]

def test_parse_long_reset_window():
    seconds=ow._parse_reset_seconds(
        'Rate limit reached. Please try again in 21h34m6.32s.'
    )
    assert seconds is not None
    assert 77640 < seconds < 77650

def test_parse_millisecond_reset_window():
    seconds=ow._parse_reset_seconds(
        'Rate limit reached. Please try again in 2039ms.'
    )
    assert 2.03 < seconds < 2.05

def test_fallback_moves_to_second_model_on_429(monkeypatch):
    monkeypatch.setattr(
        ow,
        "_ordered_models",
        lambda:["gpt-5.6-luna","gpt-5.6-terra"],
    )
    monkeypatch.setattr(ow,"_model_cooldown_remaining",lambda model:0.0)
    monkeypatch.setattr(
        ow,
        "_mark_model_rate_limited",
        lambda model,msg:{"reset_seconds":60,"blocked_until_unix":time.time()+60},
    )
    monkeypatch.setattr(ow,"_mark_model_success",lambda model:None)

    calls=[]
    def fake_request(payload,key,max_attempts=None):
        calls.append(payload["model"])
        if payload["model"]=="gpt-5.6-luna":
            raise RuntimeError("openai_http_429: rate limit reached")
        return {
            "id":"resp_1",
            "model":"gpt-5.6-terra",
            "output":[],
            "status":"completed",
        }

    monkeypatch.setattr(ow,"_request_json",fake_request)

    response,attempts,errors=ow._web_search_once(
        {
            "market":"construction",
            "target_customer":"concrete contractors",
            "problem":"estimating workflow",
            "offer":"AI bid workflow",
            "business_model":"subscription",
        },
        "pricing",
        ["construction","concrete","estimating","workflow"],
        "key",
    )

    assert response["model"]=="gpt-5.6-terra"
    assert calls==["gpt-5.6-luna","gpt-5.6-terra"]
    assert attempts[0]["status"]=="rate_limited"
    assert attempts[1]["status"]=="success"
    assert errors==[]

def test_cooldown_skips_model_without_request(monkeypatch):
    monkeypatch.setattr(ow,"_ordered_models",lambda:["gpt-5.6-luna"])
    monkeypatch.setattr(ow,"_model_cooldown_remaining",lambda model:120.0)

    called={"n":0}
    def fake_request(*a,**k):
        called["n"]+=1
        raise AssertionError("request should not occur")

    monkeypatch.setattr(ow,"_request_json",fake_request)

    response,attempts,errors=ow._web_search_once(
        {"market":"construction"},
        "pricing",
        ["construction","estimating"],
        "key",
    )

    assert response is None
    assert called["n"]==0
    assert attempts[0]["status"]=="cooldown_skip"
    assert errors
