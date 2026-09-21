from pathlib import Path

from companyos.runtime import public_research_connectors as prc
from companyos.runtime import research_candidate_synthesizer as rcs
from companyos.runtime import research_output_capture as roc
from companyos.strategy import candidate_materialization_bridge as cmb
from companyos.strategy import research_output_candidate_materializer_v2 as rom
from companyos.strategy import orchestration_candidate_extractor_v2 as oce
from companyos.strategy import profit_first_evidence_pipeline as pep
from companyos.strategy import profit_first_research_pipeline as pfr
from companyos.runtime import candidate_enrichment_bridge as ceb
from companyos.runtime import research_to_execution_bridge as reb
from companyos.runtime import profit_opportunity_engine as poe
from companyos.runtime import profit_opportunity_runtime as por
from companyos.runtime import opportunity_execution_capability_bridge as oecb

CANON = Path.home() / ".companyos_runtime"


def test_profit_research_chain_uses_canonical_runtime_root():
    assert cmb.RUNTIME == CANON
    assert rom.RUNTIME == CANON
    assert oce.RUNTIME == CANON
    assert pep.RUNTIME == CANON
    assert pfr.RUNTIME == CANON
    assert ceb.RT == CANON
    assert reb.RT == CANON
    assert poe.RT == CANON
    assert por.RT == CANON
    assert oecb.RT == CANON
    assert rcs.RUNTIME == CANON
    assert roc.RUNTIME == CANON


def test_public_research_state_is_outside_git_worktree():
    assert prc.STATE_ROOT == CANON / "external_research_network"


def test_grounded_fallback_candidate_is_machine_readable_and_not_execution_ready():
    rows = [
        {
            "source": "stackexchange",
            "title": "Teams repeatedly struggle with deployment configuration",
            "summary": "Observed public technical pain-point signal.",
            "url": "https://example.invalid/evidence/1",
            "metadata": {"views": 400, "answers": 8},
        }
    ]
    out = rcs.fallback_candidates(
        subject="find profitable automation opportunities",
        topic="business operations problem",
        source_rows=rows,
        max_candidates=1,
    )
    assert len(out) == 1
    c = out[0]
    assert c["execution_ready"] is False
    assert c["readiness"] == 0.0
    assert c["hypothesis_only"] is True
    assert c["evidence_count"] == 1
    assert c["source_urls"] == ["https://example.invalid/evidence/1"]
    assert c["evidence_confidence"] <= 25
    assert c["evidence_uncertainty"] >= 80
    assert cmb.looks_like_candidate(c) is True
    assert cmb.normalize_candidate(c, "test") is not None
    assert pep.normalize_candidate(c, "test") is not None


def test_reasoner_candidate_cannot_smuggle_unobserved_source_url():
    rows = [
        {
            "source": "github",
            "title": "Observed repo",
            "summary": "Observed source",
            "url": "https://example.invalid/allowed",
            "metadata": {},
        }
    ]
    c = rcs.normalize_candidate(
        {
            "name": "Grounded candidate",
            "sector": "software",
            "business_model": "subscription",
            "description": "A source-grounded hypothesis.",
            "market_demand": 60,
            "expected_profit": 50,
            "probability_of_success": 35,
            "margin": 65,
            "evidence_sources": [
                {"url": "https://example.invalid/not-observed", "source": "fake"}
            ],
        },
        topic="software",
        source_rows=rows,
        subject="research",
        origin="test",
    )
    assert c is not None
    assert "https://example.invalid/not-observed" not in c["source_urls"]
    assert c["source_urls"] == ["https://example.invalid/allowed"]
    assert c["execution_ready"] is False


def test_specialist_result_capture_entrypoint_exists():
    assert callable(roc.persist_specialist_result)
