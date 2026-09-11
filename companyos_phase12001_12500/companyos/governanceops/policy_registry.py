class PolicyRegistry:
    def compile(self, policies):
        rows={}
        for p in policies or []:
            rows[p.get("policy_id")]={
                "name":p.get("name"),
                "version":p.get("version","1.0"),
                "owner":p.get("owner","governance"),
                "mandatory":bool(p.get("mandatory",True)),
                "controls":list(p.get("controls",[]))
            }
        return rows
