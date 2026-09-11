class CapabilityDiscovery:
    def discover(self, connectors):
        caps={}
        for c in connectors or []:
            if not c.get("enabled",True): continue
            for cap in c.get("capabilities",[]):
                caps.setdefault(cap,[]).append(c.get("name"))
        return caps
