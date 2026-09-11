class ConnectorPolicy:
    def evaluate(self, connector, action):
        caps=set(connector.get("capabilities",[]))
        required=action.get("capability")
        permitted=(required in caps) if required else True
        read_only=bool(connector.get("metadata",{}).get("read_only",False))
        if read_only and action.get("write",False):
            permitted=False
        return {"permitted":permitted,"read_only":read_only,"required_capability":required}
