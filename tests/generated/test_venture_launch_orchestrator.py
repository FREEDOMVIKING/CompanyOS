from companyos.runtime.venture_launch_orchestrator import VentureLaunchOrchestrator
from companyos.connectors.hosting_router import HostingRouter
def test_refuses_unqualified(tmp_path):
    r=VentureLaunchOrchestrator(tmp_path).launch({"id":"x","title":"No"});assert r["reason"]=="not_execution_qualified"
def test_preserves_manual_gate(tmp_path):
    r=VentureLaunchOrchestrator(tmp_path).launch({"execution_qualified":True,"requires_manual_approval":True});assert r["reason"]=="manual_approval_required"
def test_launch_feedback(monkeypatch,tmp_path):
    monkeypatch.setattr(HostingRouter,"health",lambda s:{"healthy":True})
    monkeypatch.setattr(HostingRouter,"deploy_directory",lambda s,p,d,b:{"provider":"cloudflare","deployment_id":"D","url":"https://v.pages.dev"})
    r=VentureLaunchOrchestrator(tmp_path).launch({"id":"o1","title":"Useful Service","execution_qualified":True,"offer":"Save time"})
    assert r["status"]=="launched" and (tmp_path/".companyos_runtime"/"outcome_evidence_queue.jsonl").exists()
def test_escapes_html(monkeypatch,tmp_path):
    monkeypatch.setattr(HostingRouter,"health",lambda s:{"healthy":True})
    monkeypatch.setattr(HostingRouter,"deploy_directory",lambda s,p,d,b:{"url":"https://x","deployment_id":"1"})
    VentureLaunchOrchestrator(tmp_path).launch({"execution_qualified":True,"title":"<script>x</script>"})
    assert "<script>x</script>" not in next((tmp_path/"generated_sites").rglob("index.html")).read_text()
