from companyos.runtime.self_code_provenance import classify
def test_auto(): assert classify("Promote self-evolution candidate 123")=="autonomous"
def test_manual(): assert classify("fix workforce launcher import path")=="manual_or_installer"
def test_unknown(): assert classify("misc change")=="unknown"
