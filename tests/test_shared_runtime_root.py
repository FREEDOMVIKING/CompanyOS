from pathlib import Path

from companyos.runtime.runtime_control import UnifiedRuntimeControl
from companyos.runtime.runtime_status import RuntimeStatus
from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.end_to_end_qualification import EndToEndQualification


def test_control_plane_uses_shared_home_runtime_root():
    expected = Path.home() / ".companyos_runtime"
    root = Path.home() / "companyos"

    assert UnifiedRuntimeControl(root).runtime_root == expected
    assert RuntimeStatus(root).runtime_root == expected
    assert LaunchHealthSnapshot(root).runtime_root == expected
    assert LaunchReadinessAudit(root).runtime_root == expected
    assert EndToEndQualification(root).runtime_root == expected
