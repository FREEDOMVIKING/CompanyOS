from __future__ import annotations
import argparse, ipaddress, json, os, re, shutil, socket, subprocess, time
from pathlib import Path
from typing import Any
from companyos.runtime import remote_runtime_fabric as fabric

RT=Path.home()/".companyos_runtime"
STATE=RT/"local_lan_host_discovery_state.json"
DISCOVERED=RT/"local_lan_devices.json"
INTERVAL=max(60,int(os.getenv("COMPANYOS_LAN_DISCOVERY_SECONDS","300")))
AUTO_ENROLL=os.getenv("COMPANYOS_LAN_AUTO_ENROLL_AUTHORIZED","1")=="1"
SSH_PORTS=(22,8022)

def atomic(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp")
    t.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    t.replace(path)
    try:path.chmod(0o600)
    except Exception:pass

def run(cmd,timeout=20):
    return subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False,timeout=timeout)

def is_local_address(value:str)->bool:
    try:
        ip=ipaddress.ip_address(value)
        return bool(ip.is_private or ip.is_link_local)
    except ValueError:
        return value.endswith(".local") or value=="localhost"

def _private_ipv4(value:str):
    try:
        ip=ipaddress.ip_address(str(value).strip())
        return str(ip) if ip.version==4 and ip.is_private and not ip.is_loopback else None
    except Exception:
        return None

def _safe24(ip_value:str):
    ip=_private_ipv4(ip_value)
    if not ip:return None
    try:return str(ipaddress.ip_network(f"{ip}/24",strict=False))
    except Exception:return None

def _socket_source_ip():
    # Android-safe fallback: choose the active route and read the local
    # source address without needing root/netlink access.
    for target in (("1.1.1.1",53),("8.8.8.8",53)):
        sock=None
        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            sock.connect(target)
            ip=sock.getsockname()[0]
            good=_private_ipv4(ip)
            if good:return good
        except Exception:
            pass
        finally:
            try:
                if sock:sock.close()
            except Exception:
                pass
    return None

def _termux_wifi_ip():
    cmd=shutil.which("termux-wifi-connectioninfo")
    if not cmd:return None
    try:
        p=run([cmd],8)
        if p.returncode:return None
        data=json.loads(p.stdout or "{}")
        for key in ("ip","ip_address","ipv4"):
            good=_private_ipv4(data.get(key))
            if good:return good
    except Exception:
        pass
    return None

def _getprop_ips():
    vals=[]
    gp=shutil.which("getprop")
    if not gp:return vals
    for key in (
        "dhcp.wlan0.ipaddress",
        "dhcp.wifi.ipaddress",
        "dhcp.eth0.ipaddress",
    ):
        try:
            p=run([gp,key],3)
            good=_private_ipv4((p.stdout or "").strip())
            if good:vals.append(good)
        except Exception:
            pass
    return vals

def _route_networks():
    nets=[]
    if not shutil.which("ip"):return nets

    try:
        p=run(["ip","-o","-4","addr","show"],8)
        for line in p.stdout.splitlines():
            m=re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+/\d+)",line)
            if not m:continue
            try:
                iface=ipaddress.ip_interface(m.group(1))
                if not iface.ip.is_private or iface.ip.is_loopback:continue
                net=iface.network
                if net.prefixlen < 24:
                    net=ipaddress.ip_network(f"{iface.ip}/24",strict=False)
                nets.append(str(net))
            except Exception:
                pass
    except Exception:
        pass

    try:
        p=run(["ip","-4","route","show"],8)
        for line in p.stdout.splitlines():
            for token in line.split():
                if "/" not in token:continue
                try:
                    net=ipaddress.ip_network(token,strict=False)
                    if net.version!=4 or not net.is_private:continue
                    if net.prefixlen < 24:
                        src=None
                        m=re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)",line)
                        if m:src=m.group(1)
                        net=ipaddress.ip_network(f"{src or net.network_address}/24",strict=False)
                    nets.append(str(net))
                except Exception:
                    pass
    except Exception:
        pass

    return nets

def local_networks():
    nets=list(_route_networks())

    wifi_ip=_termux_wifi_ip()
    if wifi_ip:
        n=_safe24(wifi_ip)
        if n:nets.append(n)

    for ip in _getprop_ips():
        n=_safe24(ip)
        if n:nets.append(n)

    if not nets:
        src=_socket_source_ip()
        n=_safe24(src) if src else None
        if n:nets.append(n)

    clean=[]
    for raw in nets:
        try:
            net=ipaddress.ip_network(raw,strict=False)
            if net.version!=4 or not net.is_private:continue
            if net.prefixlen < 24:
                host=next(net.hosts())
                net=ipaddress.ip_network(f"{host}/24",strict=False)
            clean.append(str(net))
        except Exception:
            pass

    return sorted(set(clean))

def neighbor_rows():
    if not shutil.which("ip"):return []
    p=run(["ip","neigh","show"],10); rows=[]
    for raw in p.stdout.splitlines():
        parts=raw.split()
        if not parts or not is_local_address(parts[0]):continue
        mac=None
        if "lladdr" in parts:
            try:mac=parts[parts.index("lladdr")+1]
            except Exception:pass
        rows.append({"ip":parts[0],"mac":mac,"source":"ip_neigh"})
    return rows

def nmap_rows(nets):
    if not shutil.which("nmap"):return []
    rows=[]
    for net in nets[:4]:
        p=run(["nmap","-sn","-n",net],90)
        for raw in p.stdout.splitlines():
            m=re.search(r"Nmap scan report for (\d+\.\d+\.\d+\.\d+)",raw)
            if m and is_local_address(m.group(1)):rows.append({"ip":m.group(1),"source":"nmap_ping"})
    return rows

def port_open(ip,port):
    try:
        with socket.create_connection((ip,port),timeout=0.25):return True
    except Exception:return False

def merge_devices(rows):
    by={}
    for r in rows:
        ip=str(r.get("ip") or "")
        if not ip or not is_local_address(ip):continue
        cur=by.setdefault(ip,{"ip":ip,"sources":[]})
        if r.get("source") and r["source"] not in cur["sources"]:cur["sources"].append(r["source"])
        if r.get("mac"):cur["mac"]=r["mac"]
    out=[]
    for ip,row in sorted(by.items()):
        try:row["hostname"]=socket.gethostbyaddr(ip)[0]
        except Exception:row["hostname"]=None
        row["ssh_ports_open"]=[p for p in SSH_PORTS if port_open(ip,p)]
        row["candidate_host"]=bool(row["ssh_ports_open"])
        row["authorized"]=False
        out.append(row)
    return out

def ssh_aliases():
    cfg=Path.home()/".ssh/config"
    if not cfg.exists():return []
    aliases=[]
    for raw in cfg.read_text(encoding="utf-8",errors="replace").splitlines():
        line=raw.strip()
        if not line or line.startswith("#") or not line.lower().startswith("host "):continue
        for tok in line.split()[1:]:
            if not any(ch in tok for ch in "*?!"):aliases.append(tok)
    return sorted(set(aliases))

def ssh_g(alias):
    if not shutil.which("ssh"):return None
    p=run(["ssh","-G",alias],10)
    if p.returncode:return None
    d={}
    for raw in p.stdout.splitlines():
        if " " not in raw:continue
        k,v=raw.split(" ",1); k=k.lower(); v=v.strip()
        if k in {"hostname","user","port"}:d[k]=v
    return d

def local_ip(host):
    if is_local_address(host):return host
    try:
        for info in socket.getaddrinfo(host,None,socket.AF_INET):
            ip=info[4][0]
            if is_local_address(ip):return ip
    except Exception:pass
    return None

def authorized_ssh_hosts():
    rows=[]
    for alias in ssh_aliases():
        cfg=ssh_g(alias)
        if not cfg:continue
        host=str(cfg.get("hostname") or alias); ip=local_ip(host)
        if not ip:continue
        p=run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=4","-o","StrictHostKeyChecking=accept-new",alias,"printf COMPANYOS_LAN_SSH_OK"],8)
        rows.append({"alias":alias,"ip":ip,"port":int(cfg.get("port") or 22),"authorized":p.returncode==0 and "COMPANYOS_LAN_SSH_OK" in p.stdout})
    return rows

def enroll(rows):
    if not AUTO_ENROLL:return []
    existing={str(n.get("ssh_target") or "") for n in fabric.inventory().get("nodes") or [] if isinstance(n,dict)}
    out=[]
    for r in rows:
        if not r.get("authorized"):continue
        alias=str(r["alias"])
        if alias in existing:
            out.append({"alias":alias,"status":"already_enrolled"}); continue
        name="lan-"+re.sub(r"[^A-Za-z0-9_.-]+","-",alias).strip("-")[:40]
        node=fabric.add_node(name,"local_lan","research_worker",alias,int(r.get("port") or 22),None,2.0)
        out.append({"alias":alias,"status":"enrolled","node":node})
    return out

def scan():
    started=time.time(); nets=local_networks()
    devices=merge_devices(neighbor_rows()+nmap_rows(nets))
    auth=authorized_ssh_hosts(); auth_by_ip={x["ip"]:x for x in auth if x.get("authorized")}
    for d in devices:
        if d["ip"] in auth_by_ip:
            d["authorized"]=True; d["ssh_alias"]=auth_by_ip[d["ip"]]["alias"]
    enrolled=enroll(auth)
    out={"schema":"companyos.local_lan_host_discovery.v69_35e","updated_at_unix":time.time(),"scan_seconds":round(time.time()-started,3),"healthy":True,"local_networks":nets,"devices":devices,"device_count":len(devices),"ssh_candidate_count":sum(1 for d in devices if d.get("candidate_host")),"authorized_ssh_hosts":auth,"authorized_ssh_host_count":sum(1 for x in auth if x.get("authorized")),"enrollment_results":enrolled,"internet_wide_scan_performed":False,"password_guessing_performed":False,"credential_harvesting_performed":False,"exploit_attempts_performed":False}
    atomic(DISCOVERED,out); atomic(STATE,{"schema":out["schema"],"updated_at_unix":out["updated_at_unix"],"healthy":True,"device_count":out["device_count"],"ssh_candidate_count":out["ssh_candidate_count"],"authorized_ssh_host_count":out["authorized_ssh_host_count"],"enrolled_count":sum(1 for x in enrolled if x.get("status")=="enrolled"),"discovery_path":str(DISCOVERED)})
    return out

def loop():
    while True:
        try:scan()
        except Exception as e:atomic(STATE,{"schema":"companyos.local_lan_host_discovery.v69_35e","healthy":False,"updated_at_unix":time.time(),"error":f"{type(e).__name__}:{str(e)[:800]}"})
        time.sleep(INTERVAL)

def main():
    p=argparse.ArgumentParser(); p.add_argument("command",choices=("scan","status","loop")); a=p.parse_args()
    if a.command=="scan":out=scan()
    elif a.command=="status":
        try:out=json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:out={"status":"not_run"}
    else:loop(); return 0
    print(json.dumps(out,indent=2,sort_keys=True,default=str)); return 0

if __name__=="__main__":raise SystemExit(main())
