import json
from pathlib import Path

from companyos.runtime import profit_to_action_closure as pta


def packet(decision=None,status=None,missing=None):
    closure={}
    if decision is not None:
        closure={
            "decision":decision,
            "evidence":{
                "coverage":1.0,
                "missing_critical":[] if missing is None else missing,
            },
        }
    row={
        "action_packet_id":"pkt-1",
        "candidate_name":"candidate-1",
        "candidate_score":80,
        "recommended_actions":[
            {"action":"perform reversible internal validation","confidence":90}
        ],
    }
    if closure:
        row["decision_closure"]=closure
    if status is not None:
        row["status"]=status
    return row


def test_no_decision_closure_is_not_executable():
    ok,reason=pta.execution_gate(packet())
    assert ok is False
    assert reason=="decision_not_promoted"


def test_continue_research_is_not_executable():
    ok,reason=pta.execution_gate(
        packet("continue_research","research_required")
    )
    assert ok is False
    assert reason=="decision_not_promoted"


def test_deprioritize_is_not_executable():
    ok,reason=pta.execution_gate(
        packet("deprioritize","deprioritized")
    )
    assert ok is False
    assert reason=="decision_not_promoted"


def test_promoted_with_missing_critical_evidence_is_not_executable():
    ok,reason=pta.execution_gate(
        packet(
            "promote_to_guarded_execution",
            "ready_for_guarded_execution",
            ["buyer_demand"],
        )
    )
    assert ok is False
    assert reason=="critical_evidence_missing"


def test_promoted_guarded_ready_packet_is_executable():
    ok,reason=pta.execution_gate(
        packet(
            "promote_to_guarded_execution",
            "ready_for_guarded_execution",
        )
    )
    assert ok is True
    assert reason=="promoted_and_guarded_ready"


def test_packets_filters_non_promoted_rows(tmp_path,monkeypatch):
    q=tmp_path/"queue.json"
    q.write_text(
        json.dumps(
            {
                "actions":[
                    packet(),
                    packet("continue_research","research_required"),
                    packet("deprioritize","deprioritized"),
                    packet(
                        "promote_to_guarded_execution",
                        "ready_for_guarded_execution",
                    ),
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(pta,"QUEUE",q)
    rows=pta.packets()
    assert len(rows)==1
    assert rows[0]["decision_closure"]["decision"]=="promote_to_guarded_execution"
