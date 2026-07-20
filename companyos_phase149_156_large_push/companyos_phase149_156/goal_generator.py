class GoalGenerator:
    """149: derive new autonomous goals from mission gaps and evidence."""
    def generate(self, mission, state):
        goals=[]
        for gap in state.get("gaps",[]):
            goals.append({"goal":f"resolve:{gap}","priority":.8,"autonomous":True})
        if not goals and mission:
            goals.append({"goal":"improve_mission_progress","priority":.6,"autonomous":True})
        return goals
