class LessonExtractor:
    """593: extract explicit lessons from venture outcomes."""

    def extract(self, before, outcome, after):
        lessons = []
        if outcome.get("mission_success") is False:
            lessons.append("mission_execution_failed")
        if outcome.get("tests_passed") is False and "tests_passed" in outcome:
            lessons.append("quality_failure")
        if float(outcome.get("activation_rate",0)) < 0.1 and "activation_rate" in outcome:
            lessons.append("weak_activation")
        if float(outcome.get("retention_rate",0)) < 0.1 and "retention_rate" in outcome:
            lessons.append("weak_retention")
        if float(outcome.get("revenue_signal",0)) <= 0 and "revenue_signal" in outcome:
            lessons.append("no_revenue_signal")
        if before != after:
            lessons.append(f"stage_advanced:{before}->{after}")
        if not lessons:
            lessons.append("insufficient_signal")
        return lessons
