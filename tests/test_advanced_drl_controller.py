from companyos.runtime.advanced_drl_controller import ACTIONS, QNetwork, STATE_DIM, reward_between


def _snap(**kw):
    raw = {
        "observed_profit": 0.0,
        "observed_revenue": 0.0,
        "observed_conversions": 0.0,
        "missing": 20,
        "probability_unestimated": 20,
        "profit_unestimated": 10,
        "business_model_unknown": 5,
        "queue": {"failed": 0},
        "orchestrations": {"completed": 0, "failed": 0},
    }
    raw.update(kw)
    return {"raw": raw, "vector": [0.0] * STATE_DIM}


def test_network_shape():
    n = QNetwork(1)
    assert len(n.forward([0.0] * STATE_DIM)) == len(ACTIONS)


def test_profit_dominates_reward():
    r, parts = reward_between(_snap(), _snap(observed_profit=500.0))
    assert r > 0
    assert parts["verified_profit"] > parts["capability_gap_reduction"]


def test_failures_penalize():
    r, _ = reward_between(_snap(), _snap(orchestrations={"completed": 0, "failed": 2}))
    assert r < 0


def test_gap_reduction_shapes_positive_reward():
    r, _ = reward_between(_snap(missing=20), _snap(missing=15))
    assert r > 0


def test_q_train_moves_selected_value():
    n = QNetwork(2)
    s = [0.1] * STATE_DIM
    before = n.forward(s)[0]
    for _ in range(30):
        n.train_one(s, 0, 3.0)
    assert n.forward(s)[0] > before
