class SystemInventory:
    EXPECTED=[
        "runtime","integrations","operations","controlplane","execution",
        "venture_factory","marketops","scaleops","growthops","orchestration","hardening"
    ]
    def inspect(self, package_root):
        from pathlib import Path
        root=Path(package_root)/"companyos"
        rows=[]
        for name in self.EXPECTED:
            p=root/name
            rows.append({"system":name,"present":p.exists(),"path":str(p)})
        return {"systems":rows,"present_count":sum(1 for r in rows if r["present"]),
                "expected_count":len(rows),"complete":all(r["present"] for r in rows)}
