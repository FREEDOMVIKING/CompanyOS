from .util import stable_id

SPECIALISTS=[
("research","Research Specialist","market evidence and opportunity research"),
("product","Product Specialist","product and offer readiness"),
("marketing","Marketing Specialist","positioning and acquisition"),
("finance","Finance Specialist","economics and forecasting"),
("operations","Operations Specialist","workflow and execution health"),
("customer","Customer Success Specialist","support and retention"),
("launch","Launch Specialist","validation and launch readiness"),
("critic","Critic Specialist","plan challenge and risk review"),
]

class AgentFactory:
    def __init__(self,db):
        self.db=db

    def ensure_company_team(self,company):
        cid=company["company_id"]
        self.db.upsert_agent(stable_id(cid,"ceo"),cid,f"{company['name']} CEO","company_ceo",{"dynamic":False})
        created=1
        for key,name,role in SPECIALISTS:
            aid=stable_id(cid,key)
            self.db.upsert_agent(aid,cid,f"{company['name']} {name}",role,{"specialty":key,"dynamic":True})
            created+=1
        return created
