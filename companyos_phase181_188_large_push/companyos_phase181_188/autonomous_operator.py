class AutonomousOperator:
    """184: execute routine reversible operating actions without human prompting."""
    SAFE={"research","write_code","run_tests","debug","delegate","retry","local_deploy","analyze","optimize","document"}
    def authorize(self,action):
        kind=str(action.get("kind",""));reversible=bool(action.get("reversible",True));bounded=bool(action.get("bounded",True))
        allowed=kind in self.SAFE and reversible and bounded
        return {"allowed":allowed,"approval_required":not allowed,"kind":kind}
