from pathlib import Path

from companyos_phase213_220 import (
    DeterministicScaffoldAdapter,
    ModelAdapter,
    ToolExecutor,
    AutonomousCodeGenerator,
)


def test_external_adapter_reports_unconfigured():
    assert ModelAdapter(command="").available is False


def test_tool_executor_blocks_unknown(tmp_path):
    result = ToolExecutor().run(["sh", "-c", "echo no"], tmp_path)
    assert result["success"] is False
    assert "command_not_allowed" in result["reason"]


def test_scaffold_generation(tmp_path):
    spec = {
        "capability": "demo",
        "module_name": "generated_demo",
    }
    result = AutonomousCodeGenerator().generate(
        DeterministicScaffoldAdapter(),
        tmp_path,
        spec,
    )
    assert result["success"] is True
    assert (tmp_path / "generated_demo" / "core.py").exists()
