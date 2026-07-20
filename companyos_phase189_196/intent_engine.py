class IntentEngine:
    """189: translate mission/state into prioritized self-directed intents."""
    def generate(self,mission,state):
        intents=[]
        for gap in state.get("gaps",[]):
            intents.append({"intent":f"resolve:{gap}","priority":.9,"autonomous":True})
        for opportunity in state.get("opportunities",[]):
            intents.append({"intent":f"investigate:{opportunity}","priority":.75,"autonomous":True})
        if not intents:
            intents.append({"intent":f"advance:{mission or 'company_mission'}","priority":.6,"autonomous":True})
        return intents
