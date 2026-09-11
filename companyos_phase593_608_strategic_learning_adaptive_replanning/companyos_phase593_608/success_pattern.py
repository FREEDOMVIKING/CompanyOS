from collections import Counter

class SuccessPattern:
    """601: summarize repeated success signals."""

    def detect(self, lesson_sets):
        c = Counter()
        for lessons in lesson_sets:
            for lesson in lessons:
                if str(lesson).startswith("stage_advanced:"):
                    c[lesson] += 1
        return [{"pattern":k,"count":v} for k,v in c.most_common() if v >= 2]
