import json
from pathlib import Path
from companyos.runtime import autonomous_evidence_acquisition as aea

def _write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj) + "\n", encoding="utf-8")

def _candidate(path):
    _write(path,{
        "name":"regional_construction_ai",
        "market":"construction",
        "target_customer":"regional concrete contractors",
        "problem":"estimating and bid workflow inefficiency",
        "offer":"AI bid workflow automation",
        "business_model":"subscription software",
    })

def test_generic_pricing_document_does_not_satisfy_candidate_pricing(tmp_path, monkeypatch):
    research=tmp_path/"research"; candidates=tmp_path/"candidates"
    research.mkdir(); candidates.mkdir()
    _candidate(candidates/"regional_construction_ai.json")
    _write(research/"generic_pricing.json",{
        "source_rows":[{
            "source":"example",
            "url":"https://example.com/pricing",
            "title":"Generic accounting software pricing",
            "summary":"Plans cost 25 dollars per month.",
        }]
    })
    monkeypatch.setattr(aea,"RESEARCH_DIR",research)
    monkeypatch.setattr(aea,"CANDIDATE_DIR",candidates)
    queue={"tasks":[{
        "task_id":"pricing-1",
        "candidate_name":"regional_construction_ai",
        "requirement":"pricing",
        "status":"research_required",
    }]}
    assert aea.validate_tasks(queue)==0
    assert queue["tasks"][0]["status"]=="research_required"

def test_candidate_specific_pricing_source_can_satisfy_pricing(tmp_path, monkeypatch):
    research=tmp_path/"research"; candidates=tmp_path/"candidates"
    research.mkdir(); candidates.mkdir()
    _candidate(candidates/"regional_construction_ai.json")
    _write(research/"relevant_pricing.json",{
        "source_rows":[{
            "source":"vendor",
            "url":"https://example.com/construction-bid-pricing",
            "title":"Construction contractor bid automation pricing",
            "summary":"Concrete contractors can buy estimating workflow plans priced per month.",
        }]
    })
    monkeypatch.setattr(aea,"RESEARCH_DIR",research)
    monkeypatch.setattr(aea,"CANDIDATE_DIR",candidates)
    queue={"tasks":[{
        "task_id":"pricing-2",
        "candidate_name":"regional_construction_ai",
        "requirement":"pricing",
        "status":"research_required",
    }]}
    assert aea.validate_tasks(queue)==1
    assert queue["tasks"][0]["status"]=="observed"
    assert queue["tasks"][0]["evidence_artifacts"]

def test_reconcile_invalidates_unbound_observed_evidence(tmp_path, monkeypatch):
    research=tmp_path/"research"; candidates=tmp_path/"candidates"
    research.mkdir(); candidates.mkdir()
    _candidate(candidates/"regional_construction_ai.json")
    bad=research/"bad.json"
    _write(bad,{
        "source_rows":[{
            "source":"example",
            "url":"https://example.com/unrelated",
            "title":"Consumer photo editor pricing",
            "summary":"A paid plan costs 10 dollars.",
        }]
    })
    monkeypatch.setattr(aea,"RESEARCH_DIR",research)
    monkeypatch.setattr(aea,"CANDIDATE_DIR",candidates)
    queue={"tasks":[{
        "task_id":"pricing-3",
        "candidate_name":"regional_construction_ai",
        "requirement":"pricing",
        "status":"observed",
        "evidence_artifacts":[{"path":str(bad)}],
    }]}
    assert aea.reconcile_observed_tasks(queue,"regional_construction_ai")==1
    assert queue["tasks"][0]["status"]=="research_required"
    assert "evidence_artifacts" not in queue["tasks"][0]
