class AutonomousBuilder:
    """199: choose the next reversible build action from product state."""
    def next(self,state):
        if not state.get("spec_ready"): action="create_spec"
        elif not state.get("implementation_ready"): action="implement"
        elif not state.get("tests_pass"): action="debug_and_test"
        elif not state.get("validated"): action="run_internal_validation"
        else: action="iterate_or_expand"
        return {"action":action,"autonomous":True,"reversible":True}
