from .duplicate_avoidance import DuplicateAvoidance
from .venture_template import VentureTemplate

class CompanyCreationOrchestrator:
    """686: gate and prepare new venture/company creation."""

    def prepare(self, candidate, existing):
        duplicate=DuplicateAvoidance().check(candidate,existing)
        if duplicate["duplicate_risk"]:
            return {
                "success":False,
                "status":"company_creation_blocked_duplicate_risk",
                "duplicate_check":duplicate,
            }

        template=VentureTemplate().create(
            candidate.get("name"),
            candidate.get("category","uncategorized"),
            candidate.get("thesis") or candidate.get("problem"),
        )

        return {
            "success":True,
            "status":"company_creation_packet_ready",
            "venture_template":template,
            "duplicate_check":duplicate,
            "automatic_legal_entity_creation":False,
            "automatic_external_financial_commitment":False,
        }
