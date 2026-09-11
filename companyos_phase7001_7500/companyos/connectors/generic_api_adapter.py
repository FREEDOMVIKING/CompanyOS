class GenericAPIAdapter:
    def request(self, connector, method, endpoint, payload=None, write=False):
        return {
            "connector":connector,
            "method":method.upper(),
            "endpoint":endpoint,
            "payload":payload or {},
            "write":bool(write),
            "status":"prepared"
        }
