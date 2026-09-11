import json, urllib.request, urllib.error

class HTTPProviderAdapter:
    name="http_generic"
    capabilities=["http_api","research","finance_read"]
    live_supported=True

    def execute(self, request, timeout=30, live=False):
        if not live:
            return {"success":True,"simulated":True,"adapter":self.name,"request":request}
        url=request.get("url")
        method=request.get("method","GET").upper()
        headers=dict(request.get("headers") or {})
        payload=request.get("payload")
        data=None
        if payload is not None:
            data=json.dumps(payload).encode("utf-8")
            headers.setdefault("Content-Type","application/json")
        try:
            req=urllib.request.Request(url,data=data,headers=headers,method=method)
            with urllib.request.urlopen(req,timeout=timeout) as resp:
                raw=resp.read().decode("utf-8","replace")
                try: body=json.loads(raw)
                except Exception: body=raw
                return {"success":True,"status_code":resp.status,"body":body,"adapter":self.name}
        except urllib.error.HTTPError as e:
            return {"success":False,"error_kind":"http_error","status_code":e.code,"error":str(e),"adapter":self.name}
        except Exception as e:
            return {"success":False,"error_kind":"network","error":str(e),"adapter":self.name}
