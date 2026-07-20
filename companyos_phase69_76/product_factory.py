from typing import Any, Dict
class ProductFactory:
    """71: create bounded MVP build specifications."""
    def create_spec(self, opportunity: Dict[str,Any]):
        return {"name":opportunity.get("name","unnamed"),
        "problem":opportunity.get("problem",""),"customer":opportunity.get("customer",""),
        "mvp_scope":opportunity.get("mvp_scope",["core_value_delivery"]),
        "acceptance":["core flow works","basic error handling","measurement enabled"],
        "status":"spec_ready","external_deployment":False}
