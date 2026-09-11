from collections import Counter
from typing import Dict, List


def compress_memory(events: List[Dict], keep_recent: int = 50) -> Dict:
    recent = events[-keep_recent:]
    event_types = Counter(str(e.get("type", "unknown")) for e in events)
    outcomes = Counter(str(e.get("outcome", "unknown")) for e in events)
    lessons = []
    seen = set()
    for event in reversed(events):
        lesson = event.get("lesson")
        if lesson and lesson not in seen:
            seen.add(lesson)
            lessons.append(lesson)
        if len(lessons) >= 25:
            break
    return {
        "total_events": len(events),
        "event_type_counts": dict(event_types),
        "outcome_counts": dict(outcomes),
        "durable_lessons": list(reversed(lessons)),
        "recent_events": recent,
    }
