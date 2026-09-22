from companyos.runtime import local_lan_host_discovery as lan

def test_local_address_filter():
    assert lan.is_local_address("192.168.1.5")
    assert lan.is_local_address("10.0.0.8")
    assert lan.is_local_address("172.16.4.2")
    assert not lan.is_local_address("8.8.8.8")

def test_merge_devices_marks_ssh_candidates(monkeypatch):
    monkeypatch.setattr(lan.socket,"gethostbyaddr",lambda ip:("device.local",[],[]))
    monkeypatch.setattr(lan,"port_open",lambda ip,p:p==22)
    rows=lan.merge_devices([{"ip":"192.168.1.10","source":"ip_neigh"}])
    assert rows[0]["candidate_host"] is True
    assert rows[0]["ssh_ports_open"]==[22]
