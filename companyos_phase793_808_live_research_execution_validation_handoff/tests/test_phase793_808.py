from pathlib import Path
import tempfile
from companyos_phase793_808 import (
    RuntimeResearchGuard,
    QualityHandoffGate,
    RuntimeStatus,
)

def test_guard():
    assert RuntimeResearchGuard().should_run({"mission_id":"m","mission_type":"research"}) is True

def test_gate():
    r=QualityHandoffGate().evaluate({
        "lifecycle_evidence":{"validation_candidate_ready":True,"research_confidence":0.8},
        "packet":{"confidence":0.8},
    })
    assert r["passed"] is True

def test_runtime():
    assert RuntimeStatus().status()["status"]=="phase808_live_research_execution_validation_handoff_ready"
