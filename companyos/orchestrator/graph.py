from typing import Dict, List

def build_graph(ventures: List[Dict], tasks: List[Dict], agents: Dict, roadmap: List[Dict], events: List[Dict]) -> Dict:
    nodes, edges = [], []
    seen = set()

    def add_node(node_id, node_type, label, data=None):
        if node_id in seen:
            return
        seen.add(node_id)
        nodes.append({"id": node_id, "type": node_type, "label": label, "data": data or {}})

    for v in ventures:
        vid = f"venture:{v.get('venture_id')}"
        add_node(vid, "venture", v.get("name") or v.get("venture_id"), v)
        for dep in v.get("dependencies", []) or []:
            edges.append({"from": f"venture:{dep}", "to": vid, "type": "depends_on"})

    for t in tasks:
        tid = f"task:{t.get('task_id')}"
        add_node(tid, "task", t.get("action") or t.get("task_id"), t)
        if t.get("venture_id"):
            edges.append({"from": f"venture:{t.get('venture_id')}", "to": tid, "type": "owns"})
        if t.get("assigned_agent"):
            edges.append({"from": f"agent:{t.get('assigned_agent')}", "to": tid, "type": "assigned_to"})

    for aid, a in agents.items():
        add_node(f"agent:{aid}", "agent", aid, a)

    for m in roadmap:
        mid = f"milestone:{m.get('milestone_id')}"
        add_node(mid, "milestone", m.get("milestone"), m)
        edges.append({"from": f"venture:{m.get('venture_id')}", "to": mid, "type": "has_milestone"})

    for i, e in enumerate(events[-100:]):
        eid = f"event:{i}:{e.get('timestamp','')}"
        add_node(eid, "event", e.get("type","event"), e)

    return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}
