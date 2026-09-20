from companyos.extensions.generated.experiment_comparison_engine import CAPABILITY_ID, capability_manifest, evaluate


def test_manifest_and_id():
    manifest = capability_manifest()
    assert CAPABILITY_ID == "experiment_comparison_engine"
    assert manifest["id"] == CAPABILITY_ID
    assert manifest["pure"] is True
    assert manifest["side_effects"] == []


def test_comparison_uses_only_observed_values():
    result = evaluate({
        "metric_directions": {"conversion": "higher", "cost_per_success": "lower"},
        "experiments": [
            {"id": "a", "name": "A", "metrics": {"conversion": 0.20, "cost_per_success": 12}},
            {"id": "b", "name": "B", "metrics": {"conversion": 0.35, "cost_per_success": 18}},
        ],
    })
    assert result["decision"] == "ranked_on_observed_metrics"
    assert result["shared_metrics"] == ["conversion", "cost_per_success"]
    assert result["ranking"] == ["a", "b"]
    assert result["evidence_summary"]["fabricated_values"] is False
    assert result["evidence_summary"]["probabilities_estimated"] is False


def test_missing_shared_evidence_is_not_ranked():
    result = evaluate({
        "experiments": [
            {"id": "a", "observations": [{"metric": "retention", "value": 0.4}]},
            {"id": "b", "observations": [{"metric": "activation", "value": 0.7}]},
        ]
    })
    assert result["decision"] == "insufficient_comparable_evidence"
    assert result["ranking"] == []
    assert all(item["observed_metric_index"] is None for item in result["comparisons"])


def test_invalid_numeric_values_are_ignored_without_invention():
    result = evaluate({
        "experiments": [{
            "id": "a",
            "metrics": {"conversion": [0.1, "unknown", None, True]},
        }]
    })
    metric = result["comparisons"][0]["metrics"]["conversion"]
    assert metric["value"] == 0.1
    assert metric["observation_count"] == 1
    assert result["evidence_summary"]["probabilities_estimated"] is False
