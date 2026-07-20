from companyos_phase253_260.repair_controller import RepairController

def test_repair_prompt_includes_current_files(tmp_path):
    module = "generated_demo"
    (tmp_path/module).mkdir()
    (tmp_path/module/"__init__.py").write_text("from .core import f\n")
    (tmp_path/module/"core.py").write_text("def f(): return 1\n")
    (tmp_path/"tests").mkdir()
    (tmp_path/"tests"/"test_generated_demo.py").write_text("from generated_demo import f\n")

    p = RepairController().make_prompt(
        {"task":"x"},
        {"success":False,"stage":"tests"},
        1,
        workspace=tmp_path,
        module_name=module,
        targeted_test="tests/test_generated_demo.py",
    )
    assert p["current_generated_files"]
    assert p["required_layout"]["implementation"] == "generated_demo/core.py"
