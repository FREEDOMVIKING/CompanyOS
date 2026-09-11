class ProviderExecutor:
    def execute(self, adapter, request, live=False, timeout=30):
        if adapter is None:
            return {"success":False,"error_kind":"provider_unavailable","error":"adapter_not_found"}
        if live and not getattr(adapter,"live_supported",False):
            return {"success":False,"error_kind":"live_not_supported","adapter":adapter.name}
        return adapter.execute(request,timeout=timeout,live=live)
