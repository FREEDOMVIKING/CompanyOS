from pathlib import Path
from tempfile import TemporaryDirectory
from companyos.runtime.authority_aware_launch_bridge import has_real_deployment_evidence

def test_no_deployment_evidence_for_plain_site():
    with TemporaryDirectory() as td:
        p=Path(td)
        (p/"index.html").write_text("ok")
        assert has_real_deployment_evidence([p]) is False

def test_real_deployment_result_detected():
    with TemporaryDirectory() as td:
        p=Path(td)
        q=p/"companyos_progress"
        q.mkdir()
        (q/"deployment_result_abc.json").write_text("{}")
        assert has_real_deployment_evidence([p]) is True
