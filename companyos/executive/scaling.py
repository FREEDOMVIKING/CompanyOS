from .models import Venture


def recommend_scale_action(v: Venture) -> str:
    demand = float(v.metrics.get("demand", 0.0))
    margin = float(v.metrics.get("margin", 0.0))
    retention = float(v.metrics.get("retention", 0.0))
    health = (demand + margin + retention + v.progress + v.confidence) / 5.0

    if v.blocked or v.failure_probability >= 0.75:
        return "stabilize"
    if v.stage in {"operations", "scale"} and health >= 0.72 and v.risk <= 0.45:
        return "scale_up"
    if health < 0.35 or v.risk >= 0.75:
        return "reduce_exposure"
    if v.stage in {"discovery", "validation"}:
        return "validate_next"
    return "hold_and_measure"
