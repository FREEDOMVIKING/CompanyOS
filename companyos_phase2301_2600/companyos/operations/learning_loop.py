class OrganizationalLearningLoop:
    def learn(self, experiments, decisions):
        lessons=[]
        for e in experiments or []:
            lessons.append({
                "source":"experiment",
                "name":e.get("name"),
                "lesson":"scale" if e.get("success") else "revise_or_stop"
            })
        for d in decisions or []:
            lessons.append({
                "source":"decision",
                "name":d.get("name","decision"),
                "lesson":d.get("outcome","observe")
            })
        return lessons
