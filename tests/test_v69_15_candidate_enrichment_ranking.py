import json
from pathlib import Path

from companyos.runtime import candidate_enrichment_bridge as ceb
from companyos.runtime import profit_opportunity_engine as poe


def _candidate(name="Portable candidate"):
    return {
        "schema": "companyos.profit_candidate.v69_13",
        "name": name,
        "sector": "software",
        "business_model": "subscription",
        "description": "A grounded commercial hypothesis.",
        "target_customer": "small businesses",
        "problem": "manual workflow",
        "offer": "workflow automation",
        "next_action": "Collect buyer pricing evidence.",
        "expected_profit": 88,
        "probability_of_success": 62,
        "margin": 70,
        "readiness": 0,
        "evidence_confidence": 45,
        "evidence_sources": [
            {
                "source": "public",
                "url": "https://example.com/evidence",
                "claim": "public signal",
            }
        ],
        "candidate_fingerprint": "abcdef1234567890",
        "hypothesis_only": True,
        "decision_status": "research_required",
        "execution_ready": False,
    }


def test_enrichment_portable_path_accepts_runtime_outside_repo():
    p = Path.home()/".companyos_runtime/profit_first_candidates/test.json"
    assert ceb._portable_path(p) == str(p)


def test_v69_13_profit_score_is_not_silently_reinterpreted_as_dollars(tmp_path):
    src = tmp_path/"candidate.json"
    src.write_text(json.dumps(_candidate()), encoding="utf-8")
    row = ceb.normalize(_candidate(), src)
    assert row is not None
    assert row["expected_profit"] == 0
    assert row["expected_profit_score"] == 88
    assert row["probability"] == 62
    assert row["evidence_count"] == 1
    assert row["hypothesis_only"] is True


def test_enrichment_output_is_idempotent(tmp_path, monkeypatch):
    research = tmp_path/"canonical_research_outputs"
    candidates = tmp_path/"profit_first_candidates"
    state = tmp_path/"candidate_enrichment_bridge_state.json"
    research.mkdir(parents=True)
    src = research/"candidate.json"
    src.write_text(json.dumps(_candidate("Stable candidate")), encoding="utf-8")

    monkeypatch.setattr(ceb, "RESEARCH", research)
    monkeypatch.setattr(ceb, "CANDIDATES", candidates)
    monkeypatch.setattr(ceb, "STATE", state)

    first = ceb.refresh_enrichments(max_age_hours=999999)
    second = ceb.refresh_enrichments(max_age_hours=999999)

    outputs = list(candidates.glob("enriched_*.json"))
    assert first["accepted"] == 1
    assert second["accepted"] == 1
    assert len(outputs) == 1
    assert first["written"] == second["written"]


def test_profit_engine_understands_v69_13_probability_but_blocks_unpromoted_hypothesis(tmp_path):
    p = tmp_path/"candidate.json"
    d = _candidate()
    o = poe.normalize(d, p)
    assert o is not None
    assert o.probability == 62
    assert o.expected_profit == 0

    reasons = poe._candidate_qualification_reasons(poe.score(o))
    assert "research_hypothesis_not_promoted" in reasons
    assert "decision_closure_not_ready" in reasons
    assert "profit_unestimated" in reasons


def test_decision_ready_candidate_can_clear_hypothesis_gate_when_economics_exist(tmp_path):
    p = tmp_path/"candidate.json"
    d = _candidate()
    d["decision_ready"] = True
    d["decision_status"] = "promote_to_guarded_execution"
    d["expected_profit_dollars"] = 5000
    d["readiness"] = 75
    o = poe.normalize(d, p)
    assert o is not None
    assert o.expected_profit == 5000
    reasons = poe._candidate_qualification_reasons(poe.score(o))
    assert "research_hypothesis_not_promoted" not in reasons
    assert "decision_closure_not_ready" not in reasons
