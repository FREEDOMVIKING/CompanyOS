#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase673_688 import (
    PortfolioStrategy,CategoryBalance,SharedResourcePool,InfrastructureReuse,
    PortfolioKPIs,ConcentrationRisk,PortfolioPriority,SuccessionEngine,
    CompanyCreationOrchestrator,PortfolioAudit
)

ventures=[
    {
        "venture_id":"v1","name":"Contractor Bid Copilot","category":"construction_saas",
        "mrr":5000,"profit":1800,"validation_score":8,"revenue_signal":7,
        "roi_score":8,"resource_efficiency":1.5,"retention_rate":0.75,
        "stagnant_cycles":0,"infrastructure_needs":["auth","billing","telemetry"]
    },
    {
        "venture_id":"v2","name":"Field Service Scheduler","category":"construction_saas",
        "mrr":1500,"profit":200,"validation_score":6,"revenue_signal":4,
        "roi_score":5,"resource_efficiency":0.8,"retention_rate":0.5,
        "stagnant_cycles":1,"infrastructure_needs":["auth","billing","telemetry"]
    }
]
for v in ventures:
    v["portfolio_score"]=PortfolioPriority().score(v)

candidate={
    "venture_id":"c1","name":"Compliance Documentation Copilot","category":"compliance_saas",
    "problem":"manual compliance documentation","thesis":"automate repetitive compliance documentation",
    "portfolio_score":8.5
}

result={
    "strategy":PortfolioStrategy().build(),
    "balance":CategoryBalance().evaluate(ventures),
    "shared_resources":SharedResourcePool().allocate(ventures),
    "infrastructure_reuse":InfrastructureReuse().recommend(ventures),
    "portfolio_kpis":PortfolioKPIs().calculate(ventures),
    "concentration":ConcentrationRisk().evaluate(ventures),
    "succession":SuccessionEngine().recommend(ventures,[candidate],max_active=2),
    "company_creation":CompanyCreationOrchestrator().prepare(candidate,ventures),
}
PortfolioAudit(Path.home()/"companyos").append("portfolio_demo",result)
print(json.dumps(result,indent=2))
