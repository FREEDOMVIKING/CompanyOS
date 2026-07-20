from companyos_phase221_228 import ContextPackager,CoderBridge,AutonomousGapBuilder

def test_context_packager(tmp_path):
    (tmp_path/"a.py").write_text("x=1\\n")
    assert ContextPackager().collect(tmp_path)["file_count"]==1

def test_bridge_unconfigured():
    assert CoderBridge(command="").configured is False

def test_gap_selection():
    g=AutonomousGapBuilder().choose([{"capability":"x","priority":1}])
    assert g["capability"]=="x"
