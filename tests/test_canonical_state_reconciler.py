from companyos.runtime.canonical_state_reconciler import stage_markers

def test_stage_marker_detection():
    from pathlib import Path
    xs=[Path("/tmp/venture_stage_build.json")]
    assert "venture_stage_build:BUILD" in stage_markers(xs)
