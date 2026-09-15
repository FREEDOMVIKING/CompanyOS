from pathlib import Path
import ast
def test_registration_exact():
    s=Path("companyos/runtime/service_supervisor.py").read_text()
    ast.parse(s)
    assert '"continuous_profit_improvement_loop"' in s
    assert '"companyos.runtime.continuous_profit_improvement_loop"' in s
    assert s.index('"continuous_profit_improvement_loop"') < s.index("return services")
def test_module_compiles():
    ast.parse(Path("companyos/runtime/continuous_profit_improvement_loop.py").read_text())
