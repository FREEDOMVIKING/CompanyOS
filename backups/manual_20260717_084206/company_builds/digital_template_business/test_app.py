#!/usr/bin/env python3

from app import get_project_summary


def test_project_summary():
    result = get_project_summary()

    assert isinstance(result, dict)
    assert result["project_name"]
    assert result["problem"]
    assert result["target_customer"]
    assert result["solution"]
    assert result["status"] == "prototype"


if __name__ == "__main__":
    test_project_summary()
    print("PROTOTYPE_TEST_PASSED")
