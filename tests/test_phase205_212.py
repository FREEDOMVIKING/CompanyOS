from companyos_phase205_212 import CapabilityGapDetector, BuildSpecGenerator, RuntimeSupervisor

def test_gap_detection(tmp_path):
    (tmp_path/"tests").mkdir()
    rows = CapabilityGapDetector().detect(
        [{"goal":"x","required_capabilities":["missing"]}], [], tmp_path
    )
    assert rows[0]["capability"] == "missing"

def test_spec_generation():
    result = BuildSpecGenerator().generate({"capability":"web research"})
    assert result["module_name"] == "generated_web_research"
    assert result["rollback_required"] is True

def test_runtime_queue(tmp_path):
    r = RuntimeSupervisor(tmp_path)
    assert r.enqueue({"id":1})["queue_depth"] == 1
    assert r.next_job()["id"] == 1
