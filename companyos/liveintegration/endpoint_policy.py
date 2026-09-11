class EndpointPolicy:
    def evaluate(self, request):
        url=str(request.get("url",""))
        method=str(request.get("method","GET")).upper()
        allowed_scheme=url.startswith("https://") or url.startswith("http://127.0.0.1") or url.startswith("http://localhost")
        read_only=method in {"GET","HEAD","OPTIONS"}
        return {
            "allowed_scheme":allowed_scheme,
            "read_only":read_only,
            "requires_approval":not read_only,
            "allowed":allowed_scheme
        }
