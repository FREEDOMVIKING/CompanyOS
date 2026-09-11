class LearningPolicy:
    def evaluate(self, lesson):
        external=bool(lesson.get("external_action_change",False))
        financial=bool(lesson.get("financial_policy_change",False))
        safety=bool(lesson.get("safety_boundary_change",False))
        gated=external or financial or safety
        return {
            "auto_learn_allowed":not gated,
            "requires_approval":gated
        }
