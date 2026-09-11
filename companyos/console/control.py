ALLOWED_ACTIONS = {"start", "stop", "restart", "status"}

def service_action(action: str) -> dict:
    if action not in ALLOWED_ACTIONS:
        raise ValueError("Unsupported action")

    from companyos.controlplane.manager import ControlPlane

    plane = ControlPlane()
    if action == "start":
        return plane.start()
    if action == "stop":
        return plane.stop()
    if action == "restart":
        return plane.restart()
    return plane.status()
