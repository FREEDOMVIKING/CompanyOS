from companyos_phase777_792 import QueryTransformer,ProviderErrorNormalizer,CompletionPolicy
def test_query_transform():
    assert QueryTransformer().transform("x","github")["type"]=="issues_code_repos"
def test_error():
    assert ProviderErrorNormalizer().normalize({"success":False,"error":"HTTP Error 403: rate limit exceeded"})["kind"]=="rate_limited"
def test_completion():
    assert CompletionPolicy().decide(0.8,True,True)["complete"] is True
