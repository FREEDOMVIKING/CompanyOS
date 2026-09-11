class StagingValidator:
    def validate(self, smoke_tests, health):
        return {
            "smoke_tests_passed": bool(smoke_tests),
            "health_passed": bool(health),
            "passed": bool(smoke_tests) and bool(health)
        }
