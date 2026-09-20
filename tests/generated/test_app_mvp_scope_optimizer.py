from companyos.extensions.generated.app_mvp_scope_optimizer import CAPABILITY_ID, capability_manifest, evaluate


def test_manifest_is_safe_and_complete():
    manifest = capability_manifest()
    assert CAPABILITY_ID == "app_mvp_scope_optimizer"
    assert manifest["id"] == CAPABILITY_ID
    assert manifest["kind"] == "safe_analytical"
    assert manifest["side_effects"] == []


def test_empty_context_does_not_fabricate_a_candidate():
    result = evaluate({})
    assert result["status"] == "ok"
    assert result["decision"] == "research_more"
    assert result["selected_candidate"] is None
    assert "candidate_records" in result["evidence_gaps"]
    assert result["recommended_scope"]["included"]


def test_candidate_is_ranked_by_supplied_evidence():
    context = {
        "profit": {"candidate_count": 2},
        "candidates": [
            {"id": "weak", "name": "Broad app", "problem": "unclear"},
            {
                "id": "strong",
                "name": "Focused workflow",
                "problem": "repeated manual intake",
                "buyer": "clinic operator",
                "value": "faster intake",
                "evidence": "five interviews",
                "price": "paid pilot",
                "workflow": "single intake flow"
            }
        ]
    }
    result = evaluate(context)
    assert result["candidate_count"] == 2
    assert result["selected_candidate"]["id"] == "strong"
    assert result["decision"] == "scope_candidate"
    assert result["selected_candidate"]["evidence_score"] == 6
    assert result["validation_plan"][2]["measure"] == "paid signal"


def test_non_mapping_context_is_handled_without_side_effects():
    result = evaluate(None)
    assert result["status"] == "ok"
    assert result["assessed_count"] == 0
