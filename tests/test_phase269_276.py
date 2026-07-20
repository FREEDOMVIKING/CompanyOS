from companyos_phase269_276 import JsonRecovery, ContractRepair, GenerationRetry

def test_fenced_json_recovery():
    result = JsonRecovery().parse(
        '```json\\n{"files":{"x.py":"x=1\\\\n"}}\\n```'
    )
    assert result["success"] is True

def test_literal_eval_recovery():
    result = JsonRecovery().parse(
        "{'files': {'x.py': 'x=1\\\\n'},}"
    )
    assert result["success"] is True

def test_artifact_contract_conversion():
    result = ContractRepair().normalize({
        "artifacts":[{"path":"x.py","content":"x=1\\n"}]
    })
    assert result["success"] is True

def test_retry_prompt_is_strict():
    result = GenerationRetry().retry_prompt({"task":"x"}, {}, 1)
    assert result["format_repair_mode"] is True
