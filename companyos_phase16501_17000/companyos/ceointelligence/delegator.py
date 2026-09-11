from .approval_classifier import ApprovalClassifier

class SpecialistDelegator:
    def delegate(self, plan, queue):
        delegated = []
        approvals = []

        for idx, task in enumerate(plan.get("tasks", []), 1):
            task = dict(task)
            task.setdefault("id", f"task_{idx}")
            task.setdefault("priority", 5)

            gate = ApprovalClassifier().classify(task)
            payload = {
                "task_id": task["id"],
                "department": task.get("department", "operations"),
                "instruction": task.get("instruction", ""),
                "success_criteria": task.get("success_criteria", []),
                "requires_approval": gate["requires_approval"],
                "approval": False,
            }

            if gate["requires_approval"]:
                approvals.append({
                    "task": task,
                    "gate": gate,
                    "status": "approval_required"
                })
                continue

            job = queue.enqueue(
                kind=task.get("kind", "analysis"),
                payload=payload,
                priority=int(task.get("priority", 5))
            )
            delegated.append(job)

        return {
            "delegated": delegated,
            "approval_queue": approvals,
            "delegated_count": len(delegated),
            "approval_count": len(approvals)
        }
