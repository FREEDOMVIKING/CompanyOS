import pytest
from companyos.runtime import provider_connector_router as p


def test_choices_text_shape():
    payload={"choices":[{"finish_reason":"stop","index":0,"text":"COMPANYOS_CLOUDFLARE_READY"}]}
    assert p._extract_cloudflare_text(payload)=="COMPANYOS_CLOUDFLARE_READY"


def test_message_content_shape():
    payload={"choices":[{"message":{"role":"assistant","content":"READY"}}]}
    assert p._extract_cloudflare_text(payload)=="READY"


def test_content_parts_shape():
    payload=[{"type":"text","text":"COMPANYOS_"},{"type":"text","text":"READY"}]
    assert p._extract_cloudflare_text(payload)=="COMPANYOS_READY"


def test_reasoning_content_fallback():
    payload={"choices":[{"message":{"content":None,"reasoning_content":"READY"}}]}
    assert p._extract_cloudflare_text(payload)=="READY"


def test_blank_success_is_rejected(monkeypatch):
    monkeypatch.setattr(
        p,
        "secrets",
        lambda:{"cloudflare_workers_ai":{"CLOUDFLARE_API_TOKEN":"test-token","CLOUDFLARE_ACCOUNT_ID":"0"*32}},
    )
    monkeypatch.setattr(p,"cf_account_id",lambda:"0"*32)
    monkeypatch.setattr(
        p,
        "http",
        lambda *a,**k:(200,{"success":True,"result":{"choices":[{"message":{"content":None}}]}},{}),
    )

    with pytest.raises(RuntimeError,match="cloudflare_success_without_usable_text"):
        p.cloudflare_infer("READY",64)
