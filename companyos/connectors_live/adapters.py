import hashlib
import json
import re
from pathlib import Path
from urllib import request, error, parse
import os, smtplib
from email.message import EmailMessage
from .base import BaseConnector, ConnectorError
from .config import env_value

class SMTPConnector(BaseConnector):
    name='smtp'
    def is_configured(self):
        return self.enabled and all([
            env_value(self.config.get('host_env')),
            env_value(self.config.get('username_env')),
            env_value(self.config.get('password_env')),
            env_value(self.config.get('from_email_env')),
        ])
    def _execute(self,action,payload):
        if action!='send_email':
            return {'ok':False,'status':'unsupported_action'}
        msg=EmailMessage()
        msg['From']=env_value(self.config.get('from_email_env'))
        msg['To']=payload['to']
        msg['Subject']=payload.get('subject','')
        msg.set_content(payload.get('body',''))
        host=env_value(self.config.get('host_env'))
        port=int(env_value(self.config.get('port_env'),'587'))
        with smtplib.SMTP(host,port,timeout=self.timeout) as server:
            if self.config.get('use_tls',True): server.starttls()
            server.login(env_value(self.config.get('username_env')),env_value(self.config.get('password_env')))
            server.send_message(msg)
        return {'ok':True,'status':'sent'}

class RESTConnector(BaseConnector):
    name='rest_api'
    def is_configured(self):
        return self.enabled and bool(env_value(self.config.get('base_url_env')))
    def _execute(self,action,payload):
        url=env_value(self.config.get('base_url_env')).rstrip('/')+'/'+action.lstrip('/')
        token=env_value(self.config.get('token_env'))
        headers={'Authorization':f'Bearer {token}'} if token else {}
        return self._json_request(url,payload,headers)

class HandoffConnector(BaseConnector):
    endpoint_key='handoff_url_env'
    token_key='token_env'
    def is_configured(self):
        return self.enabled and bool(env_value(self.config.get(self.endpoint_key)))
    def _execute(self,action,payload):
        url=env_value(self.config.get(self.endpoint_key))
        token=env_value(self.config.get(self.token_key))
        headers={'Authorization':f'Bearer {token}'} if token else {}
        return self._json_request(url,{'action':action,'payload':payload},headers)

class HostingConnector(HandoffConnector):
    name='hosting'
    endpoint_key='deploy_url_env'
    API_BASE='https://api.vercel.com'

    def _is_configured(self):
        token = env_value(self.config.get(self.token_key))
        return self.enabled and bool(token)

    def _scope(self, payload):
        q = {}

        team_id = payload.get('team_id') or env_value('VERCEL_TEAM_ID')
        team_slug = payload.get('team_slug') or env_value('VERCEL_TEAM_SLUG')

        if team_id:
            q['teamId'] = team_id
        elif team_slug:
            q['slug'] = team_slug

        return ('?' + parse.urlencode(q)) if q else ''

    def _project_name(self, payload):
        name = (
            payload.get('project_name')
            or payload.get('company_name')
            or payload.get('company_id')
            or payload.get('name')
            or 'companyos-site'
        )

        name = str(name).lower().strip()
        name = re.sub(r'[^a-z0-9._-]+', '-', name)
        name = re.sub(r'-{2,}', '-', name).strip('-._')

        return (name or 'companyos-site')[:100]

    def _request(self, url, data, headers):
        req = request.Request(
            url,
            data=data,
            headers=headers,
            method='POST'
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()

                if not raw:
                    return {}

                return json.loads(raw.decode())

        except error.HTTPError as exc:
            body = exc.read().decode('utf-8', 'replace')

            raise ConnectorError(
                f'Vercel HTTP {exc.code}: {body[:1000]}'
            ) from exc

    def _collect_files(self, payload):
        supplied = payload.get('files')

        if isinstance(supplied, dict) and supplied:
            files = []

            for name, content in supplied.items():

                rel = str(name).lstrip('/').replace(chr(92), '/')

                if (
                    not rel
                    or rel.startswith('../')
                    or '/../' in rel
                ):
                    raise ConnectorError(
                        f'unsafe deploy path: {name}'
                    )

                if isinstance(content, bytes):
                    data = content
                else:
                    data = str(content).encode()

                files.append((rel, data))

            return files

        raw_path = (
            payload.get('website_path')
            or payload.get('site_path')
            or payload.get('artifact_path')
            or payload.get('path')
            or payload.get('artifact')
        )

        if not raw_path:
            raise ConnectorError(
                'deploy_production requires website_path or files'
            )

        root = Path(str(raw_path)).expanduser()

        if not root.is_absolute():
            candidates = [
                Path.cwd() / root,
                Path.home() / 'companyos' / root,
            ]

            root = next(
                (x for x in candidates if x.exists()),
                candidates[0]
            )

        if not root.exists():
            raise ConnectorError(
                f'website path not found: {root}'
            )

        if root.is_file():
            return [(root.name, root.read_bytes())]

        files = []

        for f in sorted(root.rglob('*')):

            if not f.is_file():
                continue

            rel = f.relative_to(root)

            if any(
                part in {
                    '.git',
                    '.venv',
                    'node_modules',
                    '__pycache__'
                }
                for part in rel.parts
            ):
                continue

            if f.name in {
                '.env',
                '.env.local',
                '.env.production'
            }:
                continue

            files.append(
                (rel.as_posix(), f.read_bytes())
            )

        if not files:
            raise ConnectorError(
                f'no deployable files found: {root}'
            )

        return files

    def _upload_file(self, token, path, data, scope):

        sha = hashlib.sha1(data).hexdigest()

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/octet-stream',
            'x-vercel-digest': sha
        }

        try:
            self._request(
                f'{self.API_BASE}/v2/now/files{scope}',
                data,
                headers
            )

        except ConnectorError as exc:

            # Content-addressed files may already exist.
            if '409' not in str(exc):
                raise

        return {
            'file': path,
            'sha': sha
        }

    def _execute(self, action, payload):

        if action != 'deploy_production':
            return {
                'ok': False,
                'status': 'unsupported_action',
                'action': action
            }

        payload = payload or {}

        token = env_value(
            self.config.get(self.token_key)
        )

        if not token:
            raise ConnectorError(
                'COMPANYOS hosting token missing'
            )

        scope = self._scope(payload)

        files = self._collect_files(payload)

        uploaded = []

        for path, data in files:
            uploaded.append(
                self._upload_file(
                    token,
                    path,
                    data,
                    scope
                )
            )

        body = {
            'name': self._project_name(payload),
            'target': 'production',
            'files': uploaded,
            'projectSettings': {
                'framework': None
            }
        }

        encoded = json.dumps(body).encode()

        result = self._request(
            f'{self.API_BASE}/v13/deployments{scope}',
            encoded,
            {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        deployment_id = (
            result.get('id')
            or result.get('uid')
        )

        url = result.get('url')

        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        return {
            'ok': bool(deployment_id),
            'status': 'deployment_created',
            'provider': 'vercel',
            'deployment_id': deployment_id,
            'live_url': url,
            'ready_state': (
                result.get('readyState')
                or result.get('state')
                or result.get('status')
            ),
            'project_name': body['name'],
            'files_uploaded': len(uploaded)
        }

class DomainConnector(HandoffConnector):
    name='domains'
    endpoint_key='api_url_env'

class CRMConnector(HandoffConnector):
    name='crm'
    endpoint_key='api_url_env'

class AccountingConnector(HandoffConnector):
    name='accounting'
    endpoint_key='api_url_env'

class BankingConnector(HandoffConnector):
    name='banking'

class CryptoConnector(HandoffConnector):
    name='crypto'
