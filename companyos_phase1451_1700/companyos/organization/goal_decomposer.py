class GoalDecomposer:
    def decompose(self, goal):
        g=str(goal)
        return [
            {"id":"g1","goal":g,"type":"strategy","objective":"define measurable outcome and constraints"},
            {"id":"g2","goal":g,"type":"research","objective":"collect evidence and unknowns"},
            {"id":"g3","goal":g,"type":"execution","objective":"build and operate smallest viable plan"},
            {"id":"g4","goal":g,"type":"measurement","objective":"measure results and compare with target"},
            {"id":"g5","goal":g,"type":"learning","objective":"update strategy from observed outcomes"},
        ]
