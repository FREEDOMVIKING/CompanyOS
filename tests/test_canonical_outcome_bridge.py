from companyos.runtime.canonical_outcome_bridge import stage_external_evidence

def test_internal_artifacts_do_not_fake_external_progress():
    refs=[
        {"artifact":"/tmp/x.research.json","result_status":"evidence_artifact_created"},
        {"artifact":"/tmp/x.plan.json","result_status":"plan_artifact_created"},
        {"artifact":"/tmp/x.build.json","result_status":"build_artifact_created"},
    ]
    assert stage_external_evidence("CUSTOMER_ACQUISITION",refs) is False

def test_explicit_outreach_result_is_detected():
    refs=[{"artifact":"/tmp/outreach_result.json","result_status":"completed"}]
    assert stage_external_evidence("CUSTOMER_ACQUISITION",refs) is True
