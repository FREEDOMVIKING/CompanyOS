class CapabilityRegistry:
    def build(self, systems):
        registry={}
        for s in systems or []:
            for cap in s.get("capabilities",[]):
                registry.setdefault(cap,[]).append({
                    "system":s.get("name"),
                    "health":float(s.get("health",1)),
                    "capacity":float(s.get("capacity",1))
                })
        return registry
