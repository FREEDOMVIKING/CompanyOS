from companyos.runtime.procurement_evidence_verifier import EDITORIAL_PATH_MARKERS

def test_blog_path_is_editorial():
    path="/blog/api-monetization/api-pricing/"
    assert any(x in path for x in EDITORIAL_PATH_MARKERS)
