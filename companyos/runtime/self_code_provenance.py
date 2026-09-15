import subprocess,time
AUTO=("self-evolution","self evolution","self_evolution","autonomous promotion","promote self","generated capability","capability expansion","recursive improvement")
MANUAL=("fix ","installer","overnight","commission","register ","align ","cloudflare","workforce")
def classify(s):
    x=s.lower()
    if any(k in x for k in AUTO): return "autonomous"
    if any(k in x for k in MANUAL): return "manual_or_installer"
    return "unknown"
def run(hours=24):
    cmd=["git","log",f"--since={hours} hours ago","--pretty=format:%H%x1f%ct%x1f%s","--","companyos/","scripts/","tests/"]
    raw=subprocess.check_output(cmd,text=True).strip()
    rows=[]
    for line in raw.splitlines() if raw else []:
        h,ts,subject=line.split("\x1f",2)
        origin=classify(subject)
        files=subprocess.check_output(["git","show","--pretty=format:","--name-status",h,"--","companyos/","scripts/","tests/"],text=True).splitlines()
        rows.append((h,ts,subject,origin,files))
    auto=[r for r in rows if r[3]=="autonomous"]
    print("===== VERIFIED AUTONOMOUS SELF-CODE =====")
    if not auto: print("None verifiable from legacy Git metadata.")
    for h,ts,subject,origin,files in auto:
        print(f"\n{h[:8]}  {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(ts)))}")
        print("Reason:",subject)
        for f in files: print(" ",f)
    print("\n===== SUMMARY =====")
    print("autonomous_verified:",len(auto))
    print("manual_or_installer_filtered:",sum(r[3]=="manual_or_installer" for r in rows))
    print("unknown_not_claimed_autonomous:",sum(r[3]=="unknown" for r in rows))
    print("total_recent_code_commits:",len(rows))
