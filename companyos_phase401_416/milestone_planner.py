class MilestonePlanner:
    """407: milestone plan for MVP delivery."""

    def build(self):
        return [
            {"milestone":"M1_spec_ready","exit":["brief approved","scope frozen"]},
            {"milestone":"M2_core_loop_ready","exit":["core workflow implemented","unit tests passing"]},
            {"milestone":"M3_rc_ready","exit":["quality gates passing","telemetry present"]},
            {"milestone":"M4_launch_ready","exit":["release checklist complete","rollback plan present"]},
        ]
