#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase657_672 import CEOFinancialBridge, FinancialHealth

root=Path.home()/"companyos"
bridge=CEOFinancialBridge(root)

metrics={
    "revenue":5000,
    "mrr":4500,
    "variable_costs":800,
    "fixed_costs":1200,
    "cash_available":20000,
    "acquisition_spend":700,
    "paying_customers":30,
    "gross_margin_rate":0.8,
    "monthly_churn_rate":0.05,
    "roi_score":7.5,
    "resource_efficiency":1.4,
}
review=bridge.review_venture("venture_demo",metrics)
print(json.dumps(review,indent=2))
print(json.dumps(FinancialHealth().evaluate(review),indent=2))
