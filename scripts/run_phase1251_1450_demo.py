import json, tempfile
from companyos.departments import ExecutiveOrchestrator

with tempfile.TemporaryDirectory() as d:
    ceo=ExecutiveOrchestrator(d)
    result=ceo.delegate(
        "Launch and operate the smallest validated business with measurable customer value",
        context={"venture_id":"demo_venture","stage":"operate","budget":5000}
    )
    print(json.dumps(result, indent=2))
