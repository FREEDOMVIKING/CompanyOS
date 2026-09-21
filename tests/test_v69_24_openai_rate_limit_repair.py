import urllib.error
from companyos.runtime import openai_web_evidence_fallback as ow

class H:
    def get(self,key):
        return "2.5" if key=="Retry-After" else None

class E:
    headers=H()

def test_retry_after_header_is_honored():
    assert ow._retry_delay_from_error(E(),"",0)==2.5

def test_retry_delay_parses_milliseconds():
    d=ow._retry_delay_from_error(
        type("E",(),{"headers":{}})(),
        "Rate limit reached. Please try again in 2039ms.",
        0,
    )
    assert 2.0 <= d <= 2.1

def test_web_search_token_budget_is_reduced():
    import inspect
    src=inspect.getsource(ow.research_candidate)
    assert '"max_output_tokens":1200' in src.replace(" ","")
