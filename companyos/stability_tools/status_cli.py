import argparse,json
from pathlib import Path

def read_json(path,default):
    try:return json.loads(Path(path).read_text())
    except Exception:return default

def load_status():
    return read_json(Path.home()/"companyos_status.txt",{})

def failed_services(data):
    return [name for name,info in data.get("services",{}).items() if info.get("enabled") and not info.get("alive")]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["lite","failed","diagnostics"])
    a=p.parse_args()
    if a.command=="diagnostics":
        root=Path.home()/"companyos"/"companyos_runtime"/"service_diagnostics"
        files=sorted(root.glob("*.json")) if root.exists() else []
        if not files:
            print("No diagnostics recorded.")
        for f in files:
            d=read_json(f,{})
            print(f"{d.get('service',f.stem)}: {d.get('status','unknown')}")
            if d.get("last_error"):print("  "+d["last_error"])
        return
    d=load_status()
    if not d:
        print("No status snapshot found.")
        return
    failed=failed_services(d)
    if a.command=="failed":
        print("\n".join(failed) if failed else "No failed services.")
        return
    active=d.get("active_service_count",0);expected=d.get("expected_service_count",0)
    healthy=bool(d.get("overall_healthy")) and not failed
    print(f"healthy: {str(healthy).lower()}")
    print(f"active: {active}")
    print(f"expected: {expected}")
    print(f"failed: {len(failed)}")
    for name in failed:print(" - "+name)

if __name__=="__main__":
    main()
