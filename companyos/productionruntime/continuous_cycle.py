class ContinuousCompanyCycle:
    STAGES=[
        "discover","research","validate","build","launch",
        "operate","optimize","portfolio_review","learn","checkpoint"
    ]

    def next(self, current_stage):
        try:
            idx=self.STAGES.index(current_stage)
        except ValueError:
            idx=0
        return self.STAGES[(idx+1)%len(self.STAGES)]

    def plan(self, current_stage):
        return {
            "current_stage":current_stage,
            "next_stage":self.next(current_stage),
            "continuous":True
        }
