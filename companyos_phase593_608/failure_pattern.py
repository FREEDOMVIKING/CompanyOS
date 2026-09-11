from collections import Counter

class FailurePattern:
    """600: summarize recurring failure lessons."""

    def detect(self, lesson_sets):
        c = Counter()
        for lessons in lesson_sets:
            for lesson in lessons:
                if lesson in (
                    "mission_execution_failed","quality_failure","weak_activation",
                    "weak_retention","no_revenue_signal"
                ):
                    c[lesson] += 1
        return [{"pattern":k,"count":v} for k,v in c.most_common() if v >= 2]
