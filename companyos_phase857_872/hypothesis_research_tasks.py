class HypothesisResearchTasks:
    def build(self,plans):
        return [{"task_type":"targeted_research","dimension":p["dimension"],"query":p["query"],
                 "success_criteria":{"minimum_new_evidence":p["minimum_new_evidence"],
                 "require_source_diversity":p["require_source_diversity"]}} for p in plans]
