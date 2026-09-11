from pathlib import Path
import sqlite3, json, shutil, time

HOME = Path.home() / "companyos"
V7 = HOME / ".companyos_enterprise_v7" / "companyos_enterprise_v7.sqlite3"
V8 = HOME / ".companyos_enterprise_v8" / "companyos_enterprise_v8.sqlite3"

def table_columns(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

def row_to_dict(row, cols):
    return {cols[i]: row[i] for i in range(len(cols))}

def pick(d, *names, default=None):
    for n in names:
        if n in d and d[n] is not None:
            return d[n]
    return default

def as_json(v):
    if isinstance(v, str):
        try:
            json.loads(v)
            return v
        except Exception:
            return json.dumps({"raw": v})
    return json.dumps(v if v is not None else {})

def main():
    print("CompanyOS V8 migration repair")
    print("V7:", V7)
    print("V8:", V8)

    if not V7.exists():
        raise SystemExit("ERROR: V7 database not found.")

    V8.parent.mkdir(parents=True, exist_ok=True)
    if V8.exists():
        backup = V8.with_suffix(f".sqlite3.pre_repair_{int(time.time())}.bak")
        shutil.copy2(V8, backup)
        print("Backed up current V8 DB:", backup)

    src = sqlite3.connect(V7)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(V8)
    dst.row_factory = sqlite3.Row
    try:
        # Ensure V8 schema exists by importing the V8 core.
        import sys
        sys.path.insert(0, str(HOME))
        from companyos.autonomous_enterprise_os_v8.core import EnterpriseOSV8
        EnterpriseOSV8(HOME)
        dst.close()
        dst = sqlite3.connect(V8)
        dst.row_factory = sqlite3.Row

        imported_companies = 0
        imported_agents = 0

        tables = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        print("V7 tables:", ", ".join(sorted(tables)))

        if "companies" in tables:
            cols = table_columns(src, "companies")
            for row in src.execute("SELECT * FROM companies"):
                d = dict(row)
                cid = str(pick(d, "company_id", "id", default="")).strip()
                name = str(pick(d, "name", "company_name", default=cid)).strip()
                if not cid or not name:
                    continue
                status = str(pick(d, "status", "state", default="MIGRATED"))
                priority = float(pick(d, "priority", "score", "portfolio_score", default=0) or 0)
                health = float(pick(d, "health", "health_score", default=100) or 100)
                payload = pick(d, "payload_json", "payload", default={})
                dst.execute(
                    "INSERT OR REPLACE INTO companies(company_id,name,status,priority,health,payload,updated_at) VALUES(?,?,?,?,?,?,datetime('now'))",
                    (cid, name, status, priority, health, as_json(payload))
                )
                imported_companies += 1

        if "agents" in tables:
            cols = table_columns(src, "agents")
            for row in src.execute("SELECT * FROM agents"):
                d = dict(row)
                aid = str(pick(d, "agent_id", "id", default="")).strip()
                if not aid:
                    continue
                cid = pick(d, "company_id", default=None)
                name = str(pick(d, "name", "agent_name", default=aid))
                role = str(pick(d, "role", "specialty", default="specialist"))
                score = float(pick(d, "score", "performance_score", default=50) or 50)
                completed = int(pick(d, "completed", "tasks_completed", default=0) or 0)
                failed = int(pick(d, "failed", "tasks_failed", default=0) or 0)
                payload = pick(d, "payload_json", "payload", default={})
                dst.execute(
                    "INSERT OR REPLACE INTO agents(agent_id,company_id,name,role,score,completed,failed,payload,updated_at) VALUES(?,?,?,?,?,?,?,?,datetime('now'))",
                    (aid, cid, name, role, score, completed, failed, as_json(payload))
                )
                imported_agents += 1

        dst.commit()
        print(f"Imported companies: {imported_companies}")
        print(f"Imported agents: {imported_agents}")

        if imported_companies == 0:
            print("WARNING: No companies imported. Dumping V7 company schema for diagnosis.")
            if "companies" in tables:
                print("companies columns:", table_columns(src, "companies"))

        # Run one V8 cycle after import.
        from companyos.autonomous_enterprise_os_v8.core import EnterpriseOSV8
        core = EnterpriseOSV8(HOME)
        result = core.cycle()
        print(json.dumps(result["status"], indent=2))

    finally:
        try: src.close()
        except Exception: pass
        try: dst.close()
        except Exception: pass

if __name__ == "__main__":
    main()
