class AgentTeamBuilder:
    """167: dynamically assemble specialist teams for autonomous initiatives."""
    def assemble(self, initiative, agents):
        needed=set(initiative.get("capabilities",[])); selected=[]; covered=set()
        ranked=sorted(agents,key=lambda a:float(a.get("reliability",0))-float(a.get("load",0)),reverse=True)
        for a in ranked:
            useful=needed & set(a.get("capabilities",[]))
            if useful-covered:
                selected.append(a.get("name")); covered |= useful
            if needed.issubset(covered): break
        return {"initiative":initiative.get("id"),"team":selected,"coverage":sorted(covered),
                "fully_covered":needed.issubset(covered),"autonomous_assembly":True}
