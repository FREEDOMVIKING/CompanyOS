from __future__ import annotations

import argparse
import copy
import json
import math
import random
import time
from pathlib import Path
from typing import Any

ROOT = (Path.home() / "companyos").resolve()
HOME_RT = Path.home() / ".companyos_runtime"
LOCAL_RT = ROOT / ".companyos_runtime"
DRL_RT = HOME_RT / "advanced_drl"
MODEL_FILE = DRL_RT / "online_network.json"
TARGET_FILE = DRL_RT / "target_network.json"
REPLAY_FILE = DRL_RT / "replay.jsonl"
STATE_FILE = DRL_RT / "state.json"
LATEST_SNAPSHOT = DRL_RT / "latest_snapshot.json"
LATEST_RECOMMENDATION = DRL_RT / "latest_recommendation.json"
OBSERVER_STATE = DRL_RT / "observer_state.json"
HISTORY_FILE = DRL_RT / "history.jsonl"

for p in (HOME_RT, LOCAL_RT, DRL_RT):
    p.mkdir(parents=True, exist_ok=True)

VERSION = "V65.98"
STATE_DIM = 20
H1 = 32
H2 = 24
ACTIONS = [
    "explore_new_business_models",
    "deepen_market_research",
    "improve_economics_estimation",
    "build_missing_capability",
    "scaffold_required_integration",
    "validate_top_candidate",
    "run_reversible_market_experiment",
    "concentrate_on_best_verified_candidate",
    "allocate_verified_capital",
]
ACTION_INDEX = {name: i for i, name in enumerate(ACTIONS)}

GAMMA = 0.97
LR = 0.002
REPLAY_MAX = 5000
BATCH_SIZE = 32
TARGET_SYNC_EVERY = 50
PRIORITY_ALPHA = 0.65
EPSILON_START = 0.30
EPSILON_END = 0.05
EPSILON_DECAY_STEPS = 1500


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return copy.deepcopy(default)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def scale(v: float, denom: float) -> float:
    try:
        return clamp(float(v) / float(denom), 0.0, 1.0)
    except Exception:
        return 0.0


def signed_log(v: float, scale_by: float = 10.0) -> float:
    try:
        x = float(v)
    except Exception:
        return 0.0
    if x == 0:
        return 0.0
    return clamp(math.copysign(math.log1p(abs(x)) / max(scale_by, 1e-9), x))


def deep_numeric(data: Any, allowed_keys: set[str]) -> list[float]:
    out: list[float] = []
    if isinstance(data, dict):
        for k, v in data.items():
            lk = str(k).lower()
            if lk in allowed_keys and isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append(float(v))
            out.extend(deep_numeric(v, allowed_keys))
    elif isinstance(data, list):
        for x in data:
            out.extend(deep_numeric(x, allowed_keys))
    return out


def first_existing_json(paths: list[Path]) -> dict[str, Any]:
    for p in paths:
        if p.exists():
            x = load_json(p, {})
            if isinstance(x, dict):
                return x
    return {}


def adaptive_state() -> dict[str, Any]:
    try:
        from companyos.runtime import adaptive_capability_director as d
        x = d.load(d.STATE, {})
        if isinstance(x, dict):
            return x
    except Exception:
        pass
    return first_existing_json([
        HOME_RT / "adaptive_capability_director_state.json",
        LOCAL_RT / "adaptive_capability_director_state.json",
    ])


def queue_counts() -> dict[str, int]:
    counts = {"queued": 0, "completed": 0, "failed": 0, "running": 0}
    seen: set[str] = set()
    for root in [HOME_RT / "task_queue", LOCAL_RT / "task_queue"]:
        if not root.exists():
            continue
        for p in root.rglob("*.json"):
            try:
                d = json.loads(p.read_text())
            except Exception:
                continue
            tid = str(d.get("task_id") or d.get("id") or p)
            if tid in seen:
                continue
            seen.add(tid)
            st = str(d.get("state") or d.get("status") or "").lower()
            if st in counts:
                counts[st] += 1
    return counts


def orchestration_counts() -> dict[str, int]:
    counts = {"running": 0, "completed": 0, "failed": 0, "halted": 0}
    seen: set[str] = set()
    for root in [HOME_RT / "ceo_orchestrations", LOCAL_RT / "ceo_orchestrations"]:
        if not root.exists():
            continue
        for p in root.glob("*.json"):
            try:
                d = json.loads(p.read_text())
            except Exception:
                continue
            oid = str(d.get("orchestration_id") or p)
            if oid in seen:
                continue
            seen.add(oid)
            st = str(d.get("state") or "").lower()
            if st in counts:
                counts[st] += 1
    return counts


def verified_outcomes() -> dict[str, Any]:
    return first_existing_json([
        LOCAL_RT / "verified_outcomes/latest.json",
        HOME_RT / "verified_outcomes/latest.json",
    ])


def venture_feedback() -> dict[str, Any]:
    return first_existing_json([
        LOCAL_RT / "venture_performance_feedback.json",
        HOME_RT / "venture_performance_feedback.json",
        LOCAL_RT / "post_launch_revenue_latest.json",
        HOME_RT / "post_launch_revenue_latest.json",
    ])


def api_available() -> float:
    cap = first_existing_json([
        LOCAL_RT / "capability_expansion/state.json",
        HOME_RT / "capability_expansion/state.json",
    ])
    raw = json.dumps(cap).lower()
    if "http 429" in raw or "rate_limit_exceeded" in raw:
        return 0.0
    if cap:
        return 1.0
    return 0.5


def self_evolution_health() -> float:
    latest = first_existing_json([
        LOCAL_RT / "self_evolution_closed_loop/latest.json",
        HOME_RT / "self_evolution_closed_loop/latest.json",
        LOCAL_RT / "self_evolution/state.json",
        HOME_RT / "self_evolution/state.json",
    ])
    st = str(latest.get("status") or latest.get("last_status") or "").lower()
    if st in {"promoted", "healthy", "completed", "pass"}:
        return 1.0
    if st in {"failed", "exception", "rolled_back"}:
        return 0.0
    return 0.5


def observed_financials() -> dict[str, float]:
    docs = [
        venture_feedback(),
        verified_outcomes(),
        first_existing_json([
            LOCAL_RT / "post_launch_revenue_latest.json",
            HOME_RT / "post_launch_revenue_latest.json",
        ]),
    ]
    revenue_keys = {"observed_revenue", "verified_revenue"}
    profit_keys = {"observed_profit", "verified_profit", "realized_profit", "verified_realized_profit"}
    cost_keys = {"observed_cost", "verified_cost", "realized_cost"}
    conversion_keys = {"observed_conversions", "verified_conversions", "conversion_count"}

    revenue = sum(sum(deep_numeric(d, revenue_keys)) for d in docs)
    profit_values = [v for d in docs for v in deep_numeric(d, profit_keys)]
    cost = sum(sum(deep_numeric(d, cost_keys)) for d in docs)
    conversions = sum(sum(deep_numeric(d, conversion_keys)) for d in docs)
    profit = sum(profit_values) if profit_values else (revenue - cost if revenue or cost else 0.0)
    return {
        "observed_revenue": float(revenue),
        "observed_profit": float(profit),
        "observed_cost": float(cost),
        "observed_conversions": float(conversions),
    }


def blocker_map(st: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in st.get("top_blockers") or []:
        if isinstance(row, (list, tuple)) and len(row) >= 2:
            try:
                out[str(row[0])] = float(row[1])
            except Exception:
                pass
    return out


def snapshot() -> dict[str, Any]:
    a = adaptive_state()
    q = queue_counts()
    o = orchestration_counts()
    vo = verified_outcomes()
    fin = observed_financials()
    blockers = blocker_map(a)
    signals = vo.get("signals") or []
    verified_signal_count = len(signals) if isinstance(signals, list) else 0

    raw = {
        "timestamp_unix": time.time(),
        "candidate_count": int(a.get("candidate_count") or a.get("candidates_observed") or 0),
        "inventory": int(a.get("inventory_after") or a.get("inventory_before") or 0),
        "missing": int(a.get("missing_after") or a.get("missing_before") or 0),
        "integration_requests": int(a.get("integration_requests") or 0),
        "probability_unestimated": int(blockers.get("probability_unestimated", 0)),
        "business_model_unknown": int(blockers.get("business_model_unknown", 0)),
        "profit_unestimated": int(blockers.get("profit_unestimated", 0)),
        "verified_signal_count": int(verified_signal_count),
        "queue": q,
        "orchestrations": o,
        "api_available": api_available(),
        "self_evolution_health": self_evolution_health(),
        **fin,
    }

    vec = [
        scale(raw["candidate_count"], 100),
        scale(raw["inventory"], 500),
        scale(raw["missing"], 100),
        scale(raw["integration_requests"], 50),
        scale(raw["probability_unestimated"], 100),
        scale(raw["business_model_unknown"], 100),
        scale(raw["profit_unestimated"], 100),
        signed_log(raw["observed_revenue"], 10),
        signed_log(raw["observed_profit"], 10),
        signed_log(raw["observed_cost"], 10),
        scale(raw["observed_conversions"], 100),
        scale(raw["verified_signal_count"], 50),
        scale(q["queued"], 1500),
        scale(q["failed"], 200),
        scale(q["running"], 100),
        scale(o["running"], 100),
        scale(o["completed"], 1000),
        scale(o["failed"], 200),
        float(raw["api_available"]),
        float(raw["self_evolution_health"]),
    ]
    assert len(vec) == STATE_DIM
    row = {"version": VERSION, "raw": raw, "vector": vec}
    save_json(LATEST_SNAPSHOT, row)
    return row


def reward_between(before: dict[str, Any], after: dict[str, Any]) -> tuple[float, dict[str, float]]:
    b = before.get("raw") or {}
    a = after.get("raw") or {}
    dp = float(a.get("observed_profit", 0)) - float(b.get("observed_profit", 0))
    dr = float(a.get("observed_revenue", 0)) - float(b.get("observed_revenue", 0))
    dc = float(a.get("observed_conversions", 0)) - float(b.get("observed_conversions", 0))
    dgaps = float(b.get("missing", 0)) - float(a.get("missing", 0))
    dblock = (
        float(b.get("probability_unestimated", 0)) - float(a.get("probability_unestimated", 0))
        + float(b.get("profit_unestimated", 0)) - float(a.get("profit_unestimated", 0))
        + 0.5 * (float(b.get("business_model_unknown", 0)) - float(a.get("business_model_unknown", 0)))
    )
    dcompleted = float((a.get("orchestrations") or {}).get("completed", 0)) - float((b.get("orchestrations") or {}).get("completed", 0))
    dfailed = float((a.get("orchestrations") or {}).get("failed", 0)) - float((b.get("orchestrations") or {}).get("failed", 0))
    dqfail = float((a.get("queue") or {}).get("failed", 0)) - float((b.get("queue") or {}).get("failed", 0))

    components = {
        "verified_profit": 12.0 * math.tanh(dp / 250.0),
        "verified_revenue": 3.0 * math.tanh(dr / 250.0),
        "conversions": 0.35 * clamp(dc, -10, 10),
        "capability_gap_reduction": 0.22 * clamp(dgaps, -10, 10),
        "evidence_blocker_reduction": 0.08 * clamp(dblock, -20, 20),
        "orchestration_completion": 0.35 * clamp(dcompleted, -10, 10),
        "orchestration_failure": -0.65 * max(0.0, dfailed),
        "queue_failure": -0.08 * max(0.0, dqfail),
    }
    reward = clamp(sum(components.values()), -20.0, 20.0)
    return reward, components


class QNetwork:
    def __init__(self, seed: int = 7):
        rnd = random.Random(seed)
        self.w1 = [[rnd.uniform(-0.10, 0.10) for _ in range(STATE_DIM)] for _ in range(H1)]
        self.b1 = [0.0 for _ in range(H1)]
        self.w2 = [[rnd.uniform(-0.10, 0.10) for _ in range(H1)] for _ in range(H2)]
        self.b2 = [0.0 for _ in range(H2)]
        self.w3 = [[rnd.uniform(-0.10, 0.10) for _ in range(H2)] for _ in range(len(ACTIONS))]
        self.b3 = [0.0 for _ in ACTIONS]

    @staticmethod
    def relu(x: float) -> float:
        return x if x > 0 else 0.0

    def forward(self, s: list[float], cache: bool = False):
        z1 = [sum(w * x for w, x in zip(row, s)) + b for row, b in zip(self.w1, self.b1)]
        h1 = [self.relu(x) for x in z1]
        z2 = [sum(w * x for w, x in zip(row, h1)) + b for row, b in zip(self.w2, self.b2)]
        h2 = [self.relu(x) for x in z2]
        q = [sum(w * x for w, x in zip(row, h2)) + b for row, b in zip(self.w3, self.b3)]
        if cache:
            return q, (s, z1, h1, z2, h2)
        return q

    def train_one(self, s: list[float], action: int, target: float, weight: float = 1.0) -> float:
        q, (s0, z1, h1, z2, h2) = self.forward(s, cache=True)
        pred = q[action]
        err = pred - target
        grad = (err if abs(err) <= 1.0 else math.copysign(1.0, err)) * float(weight)

        old_w3 = list(self.w3[action])
        for j in range(H2):
            self.w3[action][j] -= LR * grad * h2[j]
        self.b3[action] -= LR * grad

        dh2 = [grad * w for w in old_w3]
        dz2 = [g if z > 0 else 0.0 for g, z in zip(dh2, z2)]
        old_w2 = [list(row) for row in self.w2]
        for i in range(H2):
            gi = dz2[i]
            for j in range(H1):
                self.w2[i][j] -= LR * gi * h1[j]
            self.b2[i] -= LR * gi

        dh1 = [sum(dz2[i] * old_w2[i][j] for i in range(H2)) for j in range(H1)]
        dz1 = [g if z > 0 else 0.0 for g, z in zip(dh1, z1)]
        for i in range(H1):
            gi = dz1[i]
            for j in range(STATE_DIM):
                self.w1[i][j] -= LR * gi * s0[j]
            self.b1[i] -= LR * gi
        return abs(err)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "state_dim": STATE_DIM,
            "actions": ACTIONS,
            "w1": self.w1, "b1": self.b1,
            "w2": self.w2, "b2": self.b2,
            "w3": self.w3, "b3": self.b3,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]):
        n = cls()
        for k in ("w1", "b1", "w2", "b2", "w3", "b3"):
            setattr(n, k, d[k])
        return n


def load_net(path: Path, seed: int) -> QNetwork:
    d = load_json(path, {})
    if d.get("state_dim") == STATE_DIM and d.get("actions") == ACTIONS:
        try:
            return QNetwork.from_dict(d)
        except Exception:
            pass
    n = QNetwork(seed)
    save_json(path, n.to_dict())
    return n


def read_replay() -> list[dict[str, Any]]:
    if not REPLAY_FILE.exists():
        return []
    rows = []
    for line in REPLAY_FILE.read_text().splitlines()[-REPLAY_MAX:]:
        try:
            x = json.loads(line)
            if isinstance(x, dict):
                rows.append(x)
        except Exception:
            pass
    return rows


def rewrite_replay(rows: list[dict[str, Any]]) -> None:
    rows = rows[-REPLAY_MAX:]
    tmp = REPLAY_FILE.with_suffix(".jsonl.tmp")
    with tmp.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    tmp.replace(REPLAY_FILE)


def state_meta() -> dict[str, Any]:
    return load_json(STATE_FILE, {"train_steps": 0, "transitions": 0, "target_syncs": 0})


def save_state(d: dict[str, Any]) -> None:
    d["updated_at_unix"] = time.time()
    d["version"] = VERSION
    save_json(STATE_FILE, d)


def epsilon(train_steps: int) -> float:
    frac = min(1.0, max(0.0, train_steps / EPSILON_DECAY_STEPS))
    return EPSILON_START + (EPSILON_END - EPSILON_START) * frac


def choose_action(s: list[float], explore: bool = False) -> dict[str, Any]:
    st = state_meta()
    net = load_net(MODEL_FILE, 7)
    q = net.forward(s)
    eps = epsilon(int(st.get("train_steps", 0)))
    if explore and random.random() < eps:
        idx = random.randrange(len(ACTIONS))
        mode = "explore"
    else:
        idx = max(range(len(q)), key=lambda i: q[i])
        mode = "greedy"
    ranked = sorted(
        [{"action": ACTIONS[i], "q": round(float(q[i]), 6)} for i in range(len(ACTIONS))],
        key=lambda x: x["q"], reverse=True,
    )
    return {"action": ACTIONS[idx], "action_index": idx, "mode": mode, "epsilon": eps, "ranked": ranked}


def append_transition(before: dict[str, Any], action: str, after: dict[str, Any], source: str) -> dict[str, Any]:
    reward, components = reward_between(before, after)
    row = {
        "timestamp_unix": time.time(),
        "source": source,
        "s": before["vector"],
        "a": ACTION_INDEX[action],
        "action": action,
        "r": reward,
        "reward_components": components,
        "s2": after["vector"],
        "done": False,
        "priority": abs(reward) + 1.0,
        "before_raw": before.get("raw", {}),
        "after_raw": after.get("raw", {}),
    }
    append_jsonl(REPLAY_FILE, row)
    rows = read_replay()
    if len(rows) > REPLAY_MAX:
        rewrite_replay(rows[-REPLAY_MAX:])
    st = state_meta()
    st["transitions"] = int(st.get("transitions", 0)) + 1
    st["last_reward"] = reward
    st["last_action"] = action
    save_state(st)
    append_jsonl(HISTORY_FILE, {"event": "transition", **row})
    return row


def train(steps: int = 25) -> dict[str, Any]:
    rows = read_replay()
    st = state_meta()
    if len(rows) < 4:
        return {"ok": False, "reason": "insufficient_replay", "replay": len(rows), "minimum": 4}

    online = load_net(MODEL_FILE, 7)
    target = load_net(TARGET_FILE, 17)
    if int(st.get("train_steps", 0)) == 0:
        target = copy.deepcopy(online)

    losses = []
    for _ in range(max(1, int(steps))):
        weights = [(float(r.get("priority", 1.0)) + 1e-5) ** PRIORITY_ALPHA for r in rows]
        batch_n = min(BATCH_SIZE, len(rows))
        idxs = random.choices(range(len(rows)), weights=weights, k=batch_n)
        for idx in idxs:
            r = rows[idx]
            s = r["s"]
            a = int(r["a"])
            reward = float(r["r"])
            s2 = r["s2"]
            online_q2 = online.forward(s2)
            next_a = max(range(len(online_q2)), key=lambda i: online_q2[i])
            target_q2 = target.forward(s2)
            y = reward + (0.0 if r.get("done") else GAMMA * target_q2[next_a])
            pr = max(float(r.get("priority", 1.0)), 1e-6)
            iw = min(1.0, (1.0 / pr) ** 0.2)
            td = online.train_one(s, a, y, iw)
            r["priority"] = td + 1e-3
            losses.append(td)

        st["train_steps"] = int(st.get("train_steps", 0)) + 1
        if st["train_steps"] % TARGET_SYNC_EVERY == 0:
            target = copy.deepcopy(online)
            st["target_syncs"] = int(st.get("target_syncs", 0)) + 1

    save_json(MODEL_FILE, online.to_dict())
    save_json(TARGET_FILE, target.to_dict())
    rewrite_replay(rows)
    st["last_mean_abs_td_error"] = sum(losses) / max(1, len(losses))
    save_state(st)
    return {
        "ok": True,
        "replay": len(rows),
        "train_steps": st["train_steps"],
        "target_syncs": st.get("target_syncs", 0),
        "mean_abs_td_error": st["last_mean_abs_td_error"],
        "epsilon": epsilon(st["train_steps"]),
    }


def map_adaptive_action(st: dict[str, Any]) -> str | None:
    selected = st.get("selected") or []
    outcomes = st.get("outcomes") or []
    if not selected:
        return None
    req = selected[0] if isinstance(selected[0], dict) else {}
    out = outcomes[0] if outcomes and isinstance(outcomes[0], dict) else {}
    kind = str(req.get("kind") or out.get("kind") or "").lower()
    action = str(out.get("action") or "").lower()
    if kind in {"integration", "external"} or "integration_scaffold" in action:
        return "scaffold_required_integration"
    if kind in {"analysis", "internal", "research"} or "generate_test_canary_promote" in action:
        return "build_missing_capability"
    return None


def event_id(st: dict[str, Any]) -> str:
    selected = st.get("selected") or []
    outcomes = st.get("outcomes") or []
    sid = selected[0].get("id") if selected and isinstance(selected[0], dict) else ""
    ost = outcomes[0].get("status") if outcomes and isinstance(outcomes[0], dict) else ""
    return "|".join([str(st.get("timestamp_unix") or st.get("updated_at_unix") or ""), str(sid), str(ost)])


def observe_once() -> dict[str, Any]:
    current = snapshot()
    ast = adaptive_state()
    obs = load_json(OBSERVER_STATE, {})
    eid = event_id(ast)
    action = map_adaptive_action(ast)
    transition = None
    previous = obs.get("last_snapshot")

    if previous and action and eid and eid != obs.get("last_event_id"):
        transition = append_transition(previous, action, current, "observed_companyos_action")

    rec = choose_action(current["vector"], explore=False)
    recommendation = {
        "version": VERSION,
        "timestamp_unix": time.time(),
        "mode": "shadow_only",
        "objective": "maximize_verified_risk_adjusted_realized_profit",
        "recommendation": rec,
        "guards": {
            "financial_actions": False,
            "wallet_transactions": False,
            "external_irreversible_actions": False,
            "deployment_gate_bypass": False,
            "credential_changes": False,
        },
    }
    save_json(LATEST_RECOMMENDATION, recommendation)
    save_json(OBSERVER_STATE, {
        "last_event_id": eid,
        "last_snapshot": current,
        "last_observed_action": action,
        "updated_at_unix": time.time(),
    })

    tr = train(steps=8) if len(read_replay()) >= 4 else {"ok": False, "reason": "warming_up"}
    result = {
        "snapshot": current,
        "observed_action": action,
        "transition_added": bool(transition),
        "transition": transition,
        "training": tr,
        "recommendation": recommendation,
    }
    append_jsonl(HISTORY_FILE, {"event": "observe", "timestamp_unix": time.time(), "summary": {
        "observed_action": action,
        "transition_added": bool(transition),
        "training_ok": bool(tr.get("ok")),
        "recommended_action": rec["action"],
    }})
    return result


def report_to_snapshot(d: dict[str, Any]) -> dict[str, Any]:
    blockers = blocker_map(d)
    raw = {
        "timestamp_unix": float(d.get("timestamp_unix") or d.get("updated_at_unix") or 0),
        "candidate_count": int(d.get("candidate_count") or d.get("candidates_observed") or 0),
        "inventory": int(d.get("inventory_after") or d.get("inventory_before") or 0),
        "missing": int(d.get("missing_after") or d.get("missing_before") or 0),
        "integration_requests": int(d.get("integration_requests") or 0),
        "probability_unestimated": int(blockers.get("probability_unestimated", 0)),
        "business_model_unknown": int(blockers.get("business_model_unknown", 0)),
        "profit_unestimated": int(blockers.get("profit_unestimated", 0)),
        "observed_revenue": 0.0,
        "observed_profit": 0.0,
        "observed_cost": 0.0,
        "observed_conversions": 0.0,
        "verified_signal_count": 0,
        "queue": {"queued": 0, "completed": 0, "failed": 0, "running": 0},
        "orchestrations": {"running": 0, "completed": 0, "failed": 0, "halted": 0},
        "api_available": 1.0,
        "self_evolution_health": 0.5,
    }
    vec = [
        scale(raw["candidate_count"], 100), scale(raw["inventory"], 500),
        scale(raw["missing"], 100), scale(raw["integration_requests"], 50),
        scale(raw["probability_unestimated"], 100), scale(raw["business_model_unknown"], 100),
        scale(raw["profit_unestimated"], 100), 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.5,
    ]
    return {"version": VERSION, "raw": raw, "vector": vec}


def bootstrap_history(limit: int = 500) -> dict[str, Any]:
    reports: list[Path] = []
    for base in [HOME_RT / "reports", LOCAL_RT / "reports"]:
        if base.exists():
            reports.extend(base.glob("v65_97_adaptive_capability_director_*.json"))
    reports = sorted(set(reports), key=lambda p: p.stat().st_mtime)[-max(2, int(limit)):]
    added = 0
    for p1, p2 in zip(reports, reports[1:]):
        d1 = load_json(p1, {})
        d2 = load_json(p2, {})
        action = map_adaptive_action(d2)
        if not action:
            continue
        append_transition(report_to_snapshot(d1), action, report_to_snapshot(d2), "historical_adaptive_director")
        added += 1
    tr = train(steps=min(100, max(10, added))) if added >= 4 else {"ok": False, "reason": "insufficient_bootstrap"}
    return {"reports": len(reports), "transitions_added": added, "training": tr}


def status() -> dict[str, Any]:
    st = state_meta()
    snap = load_json(LATEST_SNAPSHOT, {})
    rec = load_json(LATEST_RECOMMENDATION, {})
    replay = read_replay()
    return {
        "version": VERSION,
        "mode": "shadow_learning",
        "objective": "maximize_verified_risk_adjusted_realized_profit",
        "state_dim": STATE_DIM,
        "actions": ACTIONS,
        "replay_size": len(replay),
        "train_steps": int(st.get("train_steps", 0)),
        "target_syncs": int(st.get("target_syncs", 0)),
        "epsilon": epsilon(int(st.get("train_steps", 0))),
        "last_reward": st.get("last_reward"),
        "last_action": st.get("last_action"),
        "latest_snapshot": snap.get("raw"),
        "latest_recommendation": (rec.get("recommendation") or {}).get("action"),
        "controls": {
            "financial_actions": False,
            "wallet_transactions": False,
            "external_irreversible_actions": False,
            "shadow_only": True,
        },
    }


def loop(interval: int) -> None:
    while True:
        try:
            r = observe_once()
            print(json.dumps({
                "ts": time.time(),
                "observed_action": r.get("observed_action"),
                "transition_added": r.get("transition_added"),
                "training": r.get("training"),
                "recommended_action": r.get("recommendation", {}).get("recommendation", {}).get("action"),
            }, sort_keys=True), flush=True)
        except Exception as e:
            print(json.dumps({"ts": time.time(), "error": f"{type(e).__name__}: {e}"}), flush=True)
        time.sleep(max(60, int(interval)))


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot")
    rec = sub.add_parser("recommend")
    rec.add_argument("--explore", action="store_true")
    tr = sub.add_parser("train")
    tr.add_argument("--steps", type=int, default=50)
    bs = sub.add_parser("bootstrap")
    bs.add_argument("--limit", type=int, default=500)
    sub.add_parser("observe")
    sub.add_parser("status")
    lp = sub.add_parser("loop")
    lp.add_argument("--interval", type=int, default=900)
    args = ap.parse_args()

    if args.cmd == "snapshot":
        print(json.dumps(snapshot(), indent=2, sort_keys=True))
    elif args.cmd == "recommend":
        s = snapshot()
        print(json.dumps(choose_action(s["vector"], explore=args.explore), indent=2, sort_keys=True))
    elif args.cmd == "train":
        print(json.dumps(train(args.steps), indent=2, sort_keys=True))
    elif args.cmd == "bootstrap":
        print(json.dumps(bootstrap_history(args.limit), indent=2, sort_keys=True))
    elif args.cmd == "observe":
        print(json.dumps(observe_once(), indent=2, sort_keys=True))
    elif args.cmd == "status":
        print(json.dumps(status(), indent=2, sort_keys=True))
    elif args.cmd == "loop":
        loop(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
