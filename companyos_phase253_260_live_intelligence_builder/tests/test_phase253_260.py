from companyos_phase253_260 import CodeContract, ContextBudgeter, RepairController

def test_contract_accepts_files():
    assert CodeContract().normalize({"files": {"x.py": "x=1\n"}})["success"] is True

def test_contract_blocks_parent_path():
    assert CodeContract().normalize({"files": {"../x.py": "x=1\n"}})["success"] is False

def test_context_budget():
    result = ContextBudgeter().trim(
        {"files": [{"path": "a.py", "content": "x" * 100}]},
        max_chars=50,
    )
    assert result["char_count"] <= 50

def test_repair_prompt():
    assert RepairController().make_prompt(
        {"task": "x"}, {"success": False}, 1
    )["repair_mode"] is True
