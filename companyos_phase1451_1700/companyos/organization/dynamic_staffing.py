class DynamicStaffingManager:
    ROLE_MAP={
        "research":"research_specialist",
        "product":"product_builder",
        "growth":"growth_operator",
        "sales":"sales_operator",
        "finance":"financial_analyst",
        "operations":"operations_specialist",
        "customer_success":"customer_success_operator",
        "security":"security_reviewer",
    }

    def evaluate(self, workload, registry):
        active=registry.active()
        counts={}
        for a in active:
            counts[a.get("role")]=counts.get(a.get("role"),0)+1

        hires=[]
        for dept, load in (workload or {}).items():
            role=self.ROLE_MAP.get(dept,f"{dept}_specialist")
            needed=max(0,int(load)-counts.get(role,0))
            for _ in range(min(needed,3)):
                hires.append(registry.create(role,[dept,"autonomous_execution"],temporary=True))
        return hires
