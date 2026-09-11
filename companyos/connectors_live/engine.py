from pathlib import Path
from datetime import datetime, timezone
import os, uuid

from .config import companyos_home, load_config
from .registry import build_registry
from .storage import read_json, write_json, append_json

APPROVAL_ACTIONS={'purchase_domain','deploy_production','transfer_funds','sign_transaction','hire_candidate'}

class ConnectorEngine:
    def __init__(self,home=None):
        self.home=Path(home or companyos_home())
        self.runtime=self.home/'companyos_runtime'/'connectors'
        self.runtime.mkdir(parents=True,exist_ok=True)
        self.config=load_config() if home is None else self._load_home_config()
        self.registry=build_registry(self.config)

    def _load_home_config(self):
        path=self.home/'config'/'connectors.json'
        return read_json(path,{})

    def health(self):
        report={
            'phase':'21001-22000',
            'generated_at':datetime.now(timezone.utc).isoformat(),
            'connectors':{name:conn.health() for name,conn in self.registry.items()},
        }
        report['configured_count']=sum(1 for x in report['connectors'].values() if x['configured'])
        report['enabled_count']=sum(1 for x in report['connectors'].values() if x['enabled'])
        write_json(self.runtime/'health.json',report)
        return report

    def queue(self,connector,action,payload,risk='medium'):
        item={
            'action_id':str(uuid.uuid4()),
            'connector':connector,
            'action':action,
            'payload':payload,
            'risk':risk,
            'approval_required': action in APPROVAL_ACTIONS or risk in {'high','critical'},
            'status':'queued',
            'created_at':datetime.now(timezone.utc).isoformat(),
        }
        append_json(self.runtime/'actions.json',item)
        return item

    def approve(self,action_id,approved_by='owner'):
        rec={'action_id':action_id,'approved':True,'approved_by':approved_by,
             'timestamp':datetime.now(timezone.utc).isoformat()}
        append_json(self.runtime/'approvals.json',rec)
        return rec

    def execute(self,action_id):
        actions=read_json(self.runtime/'actions.json',[])
        action=next((x for x in actions if x.get('action_id')==action_id),None)
        if not action:
            return {'ok':False,'status':'action_not_found'}
        approved=any(x.get('action_id')==action_id and x.get('approved') for x in read_json(self.runtime/'approvals.json',[]))
        if action.get('approval_required') and not approved:
            return {'ok':False,'status':'approval_required','action_id':action_id}
        connector=self.registry.get(action['connector'])
        if not connector:
            return {'ok':False,'status':'connector_not_found'}
        try:
            result=connector.execute(action['action'],action['payload'])
        except Exception as exc:
            result={'ok':False,'status':'connector_error','error':str(exc)}
        record={**action,'result':result,'executed_at':datetime.now(timezone.utc).isoformat()}
        append_json(self.runtime/'executions.json',record)
        return result

    def demo_workflow(self):
        steps=[]
        steps.append(self.queue('crm','upsert_contact',{'name':'Demo Customer','email':'demo@example.com'},'low'))
        steps.append(self.queue('smtp','send_email',{'to':'demo@example.com','subject':'Demo','body':'CompanyOS connector demo'},'high'))
        steps.append(self.queue('hosting','deploy_production',{'artifact':'demo-site'},'high'))
        return {'workflow':'lead_to_launch','mode':'safe_demo','steps':steps}
