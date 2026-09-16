import pytest
from companyos.runtime import capability_expansion as ce
from companyos.runtime import capability_request_executor as cre

def test_junk_ids_rejected():
    for cid in ("x","xx","test","tmp","foo","123"):
        with pytest.raises(ValueError):
            ce.canonical_paths(cid)

def test_meaningful_id_allowed():
    mod,test=ce.canonical_paths("executable_next_action_planner")
    assert mod.endswith("executable_next_action_planner.py")
    assert test.endswith("test_executable_next_action_planner.py")

def test_semantic_replacements():
    assert cre._replacement_capability_id(
        {"gap_type":"missing_executable_next_action"}
    ) == "executable_next_action_planner"
    assert cre._replacement_capability_id(
        {"reason":"candidate is missing external evidence"}
    ) == "external_evidence_requirements_analyzer"
    assert cre._replacement_capability_id(
        {"reason":"profit unestimated"}
    ) == "profitability_estimator"
