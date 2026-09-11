import uuid

class DynamicAgentFactory:
    def spawn(self, role, capabilities=None, temporary=True, objective=None):
        return {
            "agent_id":"agent_"+uuid.uuid4().hex[:10],
            "role":role,
            "capabilities":list(capabilities or []),
            "temporary":bool(temporary),
            "objective":objective,
            "status":"active"
        }

    def fill_gaps(self, required_capabilities, registry):
        spawned=[]
        for cap in required_capabilities or []:
            if not registry.get(cap):
                spawned.append(self.spawn(f"{cap}_specialist",[cap],True,f"Fill missing capability: {cap}"))
        return spawned
