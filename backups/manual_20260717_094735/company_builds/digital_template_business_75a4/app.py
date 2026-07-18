#!/usr/bin/env python3

PROJECT_NAME = 'digital_template_business_75a4'
PROBLEM = 'To be researched'
TARGET_CUSTOMER = 'To be researched'
SOLUTION = 'Create a focused digital product or service'


def get_project_summary() -> dict:
    return {
        "project_name": PROJECT_NAME,
        "problem": PROBLEM,
        "target_customer": TARGET_CUSTOMER,
        "solution": SOLUTION,
        "status": "prototype",
    }


if __name__ == "__main__":
    print(get_project_summary())
