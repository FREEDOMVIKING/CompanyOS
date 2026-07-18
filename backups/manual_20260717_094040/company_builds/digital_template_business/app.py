#!/usr/bin/env python3

PROJECT_NAME = 'Digital Template Business'
PROBLEM = 'Small businesses need ready-made documents and workflows'
TARGET_CUSTOMER = 'Small business owners'
SOLUTION = 'A library of editable business templates and checklists'


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
