import tempfile
import unittest
from pathlib import Path

from companyos.runtime.self_evolution_backtest import (
    run_probe_pair,
    validate_probe,
)


BASELINE = '''
class Example:
    def check(self, value):
        return value
'''


CANDIDATE = '''
class Example:
    def check(self, value):
        if value < 0:
            raise ValueError("negative")
        return value
'''


class BehavioralBacktestTests(
    unittest.TestCase
):

    def test_probe_validation(self):
        probe = {
            "mode":"class_method",
            "class_name":"Example",
            "method_name":"check",
            "constructor_args":[],
            "constructor_kwargs":{},
            "args":[-1],
            "kwargs":{},
            "assertion":{
                "kind":"raises",
                "value":"ValueError",
            },
        }

        self.assertEqual(
            validate_probe(
                probe,
                CANDIDATE,
            ),
            [],
        )

    def test_before_after_gain_required(self):
        probe = {
            "mode":"class_method",
            "class_name":"Example",
            "method_name":"check",
            "constructor_args":[],
            "constructor_kwargs":{},
            "args":[-1],
            "kwargs":{},
            "assertion":{
                "kind":"raises",
                "value":"ValueError",
            },
        }

        with tempfile.TemporaryDirectory() as td:
            root=Path(td)

            pkg=root/"companyos"
            pkg.mkdir()

            (pkg/"__init__.py").write_text(
                "",
                encoding="utf-8",
            )

            target=pkg/"example.py"

            target.write_text(
                CANDIDATE,
                encoding="utf-8",
            )

            result=run_probe_pair(
                root,
                "companyos/example.py",
                BASELINE,
                CANDIDATE,
                probe,
                candidate_runs=3,
            )

        self.assertTrue(
            result["ok"],
            result,
        )

        self.assertFalse(
            result["baseline"][
                "accepted"
            ]
        )

        self.assertEqual(
            result["candidate_passes"],
            3,
        )


if __name__=="__main__":
    unittest.main()
