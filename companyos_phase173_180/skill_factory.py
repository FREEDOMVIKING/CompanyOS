class SkillFactory:
    """176: identify repeated workflows that should become reusable internal skills."""
    def propose(self, executions, threshold=3):
        counts={}
        for e in executions:
            key=str(e.get("workflow","unknown"));counts[key]=counts.get(key,0)+1
        return [{"workflow":k,"executions":v,"create_reusable_skill":v>=int(threshold),
                 "autonomous_generation_allowed":v>=int(threshold)} for k,v in counts.items()]
