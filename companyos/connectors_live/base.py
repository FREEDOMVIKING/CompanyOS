from datetime import datetime, timezone
from urllib import request, error
import json, time

class ConnectorError(RuntimeError):
    pass

class BaseConnector:
    name='base'

    def __init__(self, config):
        self.config=config or {}
        self.enabled=bool(self.config.get('enabled',False))
        self.dry_run=bool(self.config.get('dry_run',True))
        self.timeout=int(self.config.get('request_timeout_seconds',20) or 20)
        self.max_retries=int(self.config.get('max_retries',2) or 2)

    def health(self):
        return {
            'name':self.name,
            'enabled':self.enabled,
            'configured':self.is_configured(),
            'dry_run':self.dry_run,
        }

    def is_configured(self):
        return self.enabled

    def execute(self, action, payload):
        if not self.enabled:
            return {'ok':False,'status':'disabled','connector':self.name}
        if not self.is_configured():
            return {'ok':False,'status':'not_configured','connector':self.name}
        if self.dry_run:
            return {'ok':True,'status':'dry_run','connector':self.name,'action':action,'payload':payload}
        return self._execute(action,payload)

    def _json_request(self,url,payload,headers=None,method='POST'):
        body=json.dumps(payload).encode()
        hdr={'Content-Type':'application/json',**(headers or {})}
        last=None
        for attempt in range(self.max_retries+1):
            try:
                req=request.Request(url,data=body,headers=hdr,method=method)
                with request.urlopen(req,timeout=self.timeout) as resp:
                    raw=resp.read().decode()
                    return {'ok':True,'status_code':resp.status,'body':json.loads(raw) if raw else {}}
            except Exception as exc:
                last=exc
                if attempt<self.max_retries: time.sleep(min(2**attempt,4))
        raise ConnectorError(str(last))
