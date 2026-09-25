import ipaddress
from companyos.runtime import local_lan_host_discovery as lan

def test_safe24():
    assert lan._safe24("192.168.50.23")=="192.168.50.0/24"
    assert lan._safe24("10.42.7.9")=="10.42.7.0/24"
    assert lan._safe24("8.8.8.8") is None

def test_local_networks_socket_fallback(monkeypatch):
    monkeypatch.setattr(lan,"_route_networks",lambda:[])
    monkeypatch.setattr(lan,"_termux_wifi_ip",lambda:None)
    monkeypatch.setattr(lan,"_getprop_ips",lambda:[])
    monkeypatch.setattr(lan,"_socket_source_ip",lambda:"192.168.77.34")
    assert lan.local_networks()==["192.168.77.0/24"]

def test_reported_network_is_capped_to_24(monkeypatch):
    monkeypatch.setattr(lan,"_route_networks",lambda:["10.20.0.0/16"])
    monkeypatch.setattr(lan,"_termux_wifi_ip",lambda:None)
    monkeypatch.setattr(lan,"_getprop_ips",lambda:[])
    monkeypatch.setattr(lan,"_socket_source_ip",lambda:None)
    out=lan.local_networks()
    assert len(out)==1
    assert ipaddress.ip_network(out[0]).prefixlen >= 24
