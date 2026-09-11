from typing import Dict, List

def derive_playbooks(events: List[Dict], decisions: List[Dict]) -> List[Dict]:
    playbooks=[]
    lessons=[]
    for event in events:
        lesson=event.get("lesson")
        if lesson and lesson not in lessons:
            lessons.append(lesson)
    for i,lesson in enumerate(lessons[-25:],1):
        playbooks.append({
            "playbook_id":f"lesson:{i}",
            "title":lesson[:80],
            "trigger":"similar operating condition detected",
            "steps":["review prior outcome","apply lesson","measure result","record updated outcome"],
            "source":"executive_events",
        })
    if not playbooks and decisions:
        playbooks.append({
            "playbook_id":"default:decision-review",
            "title":"Review proposed executive decision before execution",
            "trigger":"new executive decision",
            "steps":["inspect rationale","check risk","verify dependencies","approve or revise"],
            "source":"generated",
        })
    return playbooks

def learning_summary(playbooks: List[Dict], events: List[Dict]) -> Dict:
    return {
        "playbook_count":len(playbooks),
        "event_count":len(events),
        "learning_ready":bool(playbooks),
    }
