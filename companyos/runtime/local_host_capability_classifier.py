from __future__ import annotations

import argparse
import ipaddress
import json
import os
import socket
import time
from pathlib import Path
from typing import Any

from companyos.runtime import local_lan_host_discovery as lan

RT = Path.home() / ".companyos_runtime"
LAN_RESULTS = RT / "local_lan_devices.json"
STATE = RT / "local_host_capability_state.json"
RESULTS = RT / "local_host_capability_results.json"

INTERVAL = max(120, int(os.getenv("COMPANYOS_LOCAL_HOST_CAPABILITY_SECONDS", "600")))

PORTS = {
    22: "ssh",
    8022: "termux_ssh",
    3389: "rdp",
    445: "smb",
    5985: "winrm_http",
    5986: "winrm_https",
    2375: "docker_plain",
    2376: "docker_tls",
    5900: "vnc",
    5000: "nas_admin_5000",
    5001: "nas_admin_5001",
}

def atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)
    try:
        path.chmod(0o600)
    except Exception:
        pass

def private_ipv4(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
        return ip.version == 4 and ip.is_private and not ip.is_loopback
    except Exception:
        return False

def open_port(ip: str, port: int, timeout: float = 0.30) -> bool:
    if not private_ipv4(ip):
        return False
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False

def self_ips() -> set[str]:
    out = set()
    try:
        x = lan._socket_source_ip()
        if x:
            out.add(str(x))
    except Exception:
        pass
    return out

def classify(device: dict[str, Any], ports: list[int], is_self: bool) -> dict[str, Any]:
    hostname = str(device.get("hostname") or "").lower()
    services = [PORTS[p] for p in ports if p in PORTS]

    score = 0
    evidence = []
    platform_hint = "unknown"
    direct_bootstrap = False
    authorization_needed = True

    if is_self:
        return {
            "score": -100,
            "platform_hint": "current_phone",
            "direct_bootstrap": False,
            "authorization_needed": False,
            "readiness": "exclude_current_phone",
            "evidence": ["current CompanyOS phone; exclude as migration target"],
            "services": services,
        }

    if 22 in ports or 8022 in ports:
        score += 80
        direct_bootstrap = True
        platform_hint = "unix_or_android"
        evidence.append("SSH service detected")

    if 5985 in ports or 5986 in ports:
        score += 65
        platform_hint = "windows"
        evidence.append("WinRM detected")

    if 3389 in ports:
        score += 35
        if platform_hint == "unknown":
            platform_hint = "windows"
        evidence.append("RDP detected")

    if 445 in ports:
        score += 30
        if platform_hint == "unknown":
            platform_hint = "windows_or_nas"
        evidence.append("SMB detected")

    if 2376 in ports:
        score += 70
        platform_hint = "docker_host"
        evidence.append("Docker TLS port detected")

    if 2375 in ports:
        score += 55
        platform_hint = "docker_host"
        evidence.append("Docker API port detected; no API call attempted")

    if 5000 in ports or 5001 in ports:
        score += 35
        if platform_hint == "unknown":
            platform_hint = "nas"
        evidence.append("NAS-style management port detected")

    if 5900 in ports:
        score += 20
        evidence.append("VNC detected")

    if any(x in hostname for x in ("desktop", "laptop", "pc-", "workstation", "server", "raspberrypi")):
        score += 15
        evidence.append("hostname resembles general-purpose computer/server")

    if not services:
        evidence.append("no recognized host-management service detected")

    if direct_bootstrap:
        readiness = "ssh_service_available"
    elif platform_hint in {"windows", "windows_or_nas"}:
        readiness = "candidate_needs_remote_management_authorization"
    elif platform_hint in {"docker_host", "nas"}:
        readiness = "candidate_needs_admin_authorization"
    else:
        readiness = "insufficient_host_evidence"

    return {
        "score": score,
        "platform_hint": platform_hint,
        "direct_bootstrap": direct_bootstrap,
        "authorization_needed": authorization_needed,
        "readiness": readiness,
        "evidence": evidence,
        "services": services,
    }

def load_lan() -> dict[str, Any]:
    if not LAN_RESULTS.exists():
        return lan.scan()
    try:
        data = json.loads(LAN_RESULTS.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("bad LAN result")
        return data
    except Exception:
        return lan.scan()

def run_scan() -> dict[str, Any]:
    lan_data = load_lan()
    devices = list(lan_data.get("devices") or [])
    me = self_ips()

    rows = []
    for d in devices:
        ip = str(d.get("ip") or "")
        if not private_ipv4(ip):
            continue

        ports = [p for p in PORTS if open_port(ip, p)]
        info = classify(d, ports, ip in me)

        rows.append({
            "ip": ip,
            "hostname": d.get("hostname"),
            "mac": d.get("mac"),
            "open_management_ports": ports,
            **info,
        })

    rows.sort(key=lambda x: (-float(x.get("score") or 0), x.get("ip") or ""))

    viable = [
        r for r in rows
        if r.get("score", 0) > 0 and r.get("platform_hint") != "current_phone"
    ]
    best = viable[0] if viable else None

    out = {
        "schema": "companyos.local_host_capability.v69_35g",
        "updated_at_unix": time.time(),
        "healthy": True,
        "network_count": len(lan_data.get("local_networks") or []),
        "device_count": len(rows),
        "candidate_count": len(viable),
        "best_candidate": best,
        "devices": rows,
        "policy": {
            "private_lan_only": True,
            "login_attempts": False,
            "password_guessing": False,
            "exploit_attempts": False,
            "automatic_use_requires_authorization": True,
        },
    }

    atomic(RESULTS, out)
    atomic(STATE, {
        "schema": out["schema"],
        "updated_at_unix": out["updated_at_unix"],
        "healthy": True,
        "device_count": out["device_count"],
        "candidate_count": out["candidate_count"],
        "best_candidate_ip": (best or {}).get("ip"),
        "best_candidate_platform_hint": (best or {}).get("platform_hint"),
        "results_path": str(RESULTS),
    })
    return out

def loop() -> None:
    while True:
        try:
            run_scan()
        except Exception as e:
            atomic(STATE, {
                "schema": "companyos.local_host_capability.v69_35g",
                "updated_at_unix": time.time(),
                "healthy": False,
                "error": f"{type(e).__name__}:{str(e)[:800]}",
            })
        time.sleep(INTERVAL)

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("scan", "status", "loop"))
    a = p.parse_args()

    if a.command == "scan":
        out = run_scan()
    elif a.command == "status":
        try:
            out = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            out = {"status": "not_run"}
    else:
        loop()
        return 0

    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
