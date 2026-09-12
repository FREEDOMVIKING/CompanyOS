import json,tempfile,sys
from pathlib import Path
ROOT = Path.home() / "companyos"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from companyos.runtime import profit_opportunity_engine as e
d={"name":"Commissioned infrastructure sourcing","profit_mechanism":"commission","next_action":"verify suppliers and a qualified buyer","expected_profit":12000,"expected_margin_pct":82,"time_to_cash_days":21,"capital_required":250,"capital_at_risk":250,"probability_success_pct":58,"evidence_count":4,"evidence_quality_pct":72,"scalability_pct":68,"reversibility_pct":95,"execution_readiness_pct":75,"complexity_pct":35,"legal_compliance_risk_pct":15}
with tempfile.TemporaryDirectory() as z:
 p=Path(z)/"x.json";p.write_text(json.dumps(d));o=e.normalize(d,p);assert o and e.score(o).score>0
bad={"name":"Use 0-100 numeric scores","instruction":"for each candidate use 0-100 numeric scores"}
with tempfile.TemporaryDirectory() as z:
 p=Path(z)/"use_0_100.json";assert e.normalize(bad,p) is None
print("COMPANYOS_PROFIT_OPPORTUNITY_ENGINE_VALIDATION=PASS")

