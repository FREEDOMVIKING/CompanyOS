from typing import Dict, List
from .models import Venture, Worker
from .prioritizer import score_venture


def assign_workers(ventures: List[Venture], workers: List[Worker]) -> Dict[str, List[str]]:
    assignments: Dict[str, List[str]] = {v.venture_id: [] for v in ventures}
    available = sorted(
        [w for w in workers if w.current_load < w.capacity],
        key=lambda w: (w.reliability, w.capacity - w.current_load),
        reverse=True,
    )
    ranked = sorted([v for v in ventures if not v.blocked], key=score_venture, reverse=True)

    for venture in ranked:
        need = max(0, int(venture.workers_requested))
        while need and available:
            best_index = max(
                range(len(available)),
                key=lambda i: _fit(available[i], venture),
            )
            worker = available.pop(best_index)
            assignments[venture.venture_id].append(worker.worker_id)
            need -= 1
    return assignments


def _fit(worker: Worker, venture: Venture) -> float:
    specialty_hint = str(venture.metrics.get("specialty", "")).lower()
    specialty_match = 1.0 if specialty_hint and specialty_hint in worker.specialty.lower() else 0.5
    free_capacity = max(0.0, worker.capacity - worker.current_load)
    return 0.45 * worker.reliability + 0.35 * free_capacity + 0.20 * specialty_match
