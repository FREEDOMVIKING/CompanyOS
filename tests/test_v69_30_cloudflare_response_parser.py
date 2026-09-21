import pytest
from companyos.runtime import provider_connector_router as p

def test_extract_cloudflare_response_field():
    assert p._extract_cloudflare_text({"response":"READY"})=="READY"

def test_extract_cloudflare_text_field():
    assert p._extract_cloudflare_text({"text":"READY"})=="READY"

def test_extract_cloudflare_choices_text():
    payload={"choices":[{"finish_reason":"stop","index":0,"text":"READY"}]}
    assert p._extract_cloudflare_text(payload)=="READY"

def test_extract_cloudflare_choices_message_content():
    payload={"choices":[{"message":{"role":"assistant","content":"READY"}}]}
    assert p._extract_cloudflare_text(payload)=="READY"

def test_extract_cloudflare_content_parts():
    payload={
        "choices":[{
            "message":{
                "content":[
                    {"type":"text","text":"COMPANYOS_"},
                    {"type":"text","text":"READY"},
                ]
            }
        }]
    }
    assert p._extract_cloudflare_text(payload)=="COMPANYOS_READY"

def test_empty_result_returns_empty():
    assert p._extract_cloudflare_text({"choices":[]})==""

def test_cloudflare_success_without_text_is_failure(monkeypatch):
    monkeypatch.setattr(
        p,
        "secrets",
        lambda:{
            "cloudflare_workers_ai":{
                "CLOUDFLARE_API_TOKEN":"test-token",
                "CLOUDFLARE_ACCOUNT_ID":"0"*32,
            }
        },
    )
    monkeypatch.setattr(p,"cf_account_id",lambda:"0"*32)
    monkeypatch.setattr(
        p,
        "http",
        lambda *a,**k:(200,{"success":True,"result":{"choices":[]}},{}),
    )

    with pytest.raises(RuntimeError,match="cloudflare_success_without_usable_text"):
        p.cloudflare_infer("READY",32)
