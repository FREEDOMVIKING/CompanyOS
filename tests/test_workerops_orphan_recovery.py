import unittest

from companyos.workerops.orphan_recovery import OrphanRecovery


class TestOrphanRecovery(unittest.TestCase):

    def test_expired_running_job_becomes_unclaimed_retry(self):
        original = {
            "job_id": "j1",
            "status": "running",
            "claimed_by": "worker-a",
            "lease_expiry_tick": 5,
        }

        result = OrphanRecovery().recover([original], tick=10)

        self.assertEqual(len(result), 1)

        recovered = result[0]

        self.assertEqual(recovered["status"], "retry")
        self.assertIsNone(recovered["claimed_by"])

        # A retry job is no longer actively leased.
        # Its lease must not be extended into the future.
        self.assertLessEqual(
            int(recovered.get("lease_expiry_tick", 0)),
            10,
        )

    def test_unexpired_running_job_is_not_recovered(self):
        job = {
            "job_id": "j2",
            "status": "running",
            "claimed_by": "worker-a",
            "lease_expiry_tick": 20,
        }

        self.assertEqual(
            OrphanRecovery().recover([job], tick=10),
            [],
        )

    def test_recovery_does_not_mutate_original_job(self):
        job = {
            "job_id": "j3",
            "status": "running",
            "claimed_by": "worker-a",
            "lease_expiry_tick": 5,
        }

        before = dict(job)

        OrphanRecovery().recover([job], tick=10)

        self.assertEqual(job, before)


if __name__ == "__main__":
    unittest.main()
