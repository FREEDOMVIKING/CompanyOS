import json, os, urllib.request, urllib.error

class HTTPJSONProvider:
    def call(self, url, payload, api_key_env=None, timeout=30):
        if not url:
            return {"success":False,"error":"missing_url"}
        headers={"Content-Type":"application/json"}
        if api_key_env:
            key=os.getenv(api_key_env)
            if not key:
                return {"success":False,"error":"missing_api_key","env":api_key_env}
            headers["Authorization"]="Bearer "+key

        req=urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body=resp.read().decode("utf-8","replace")
                try:
                    data=json.loads(body)
                except Exception:
                    data={"raw":body}
                return {
                    "success":200 <= int(resp.status) < 300,
                    "status_code":int(resp.status),
                    "data":data
                }
        except urllib.error.HTTPError as e:
            return {"success":False,"status_code":e.code,"error":"http_error"}
        except Exception as e:
            return {"success":False,"error":type(e).__name__,"message":str(e)}
