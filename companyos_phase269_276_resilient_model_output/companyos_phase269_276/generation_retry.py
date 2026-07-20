from __future__ import annotations

class GenerationRetry:
    """273: build focused retry prompts when output format is malformed."""

    def retry_prompt(self, original_payload, diagnostics, attempt):
        return {
            **original_payload,
            "format_repair_mode": True,
            "format_repair_attempt": int(attempt),
            "previous_output_diagnostics": diagnostics,
            "strict_output_requirements": [
                "Return ONLY valid JSON.",
                "Do not use markdown code fences.",
                "Do not include prose before or after JSON.",
                'Top-level object must contain "files".',
                '"files" must map relative file paths to complete string contents.',
                "Escape newlines and quotes so JSON parses correctly.",
                "Do not use absolute paths or parent-directory paths.",
            ],
            "required_example_shape": {
                "files": {
                    "generated_example/__init__.py": "from .core import example\\n",
                    "generated_example/core.py": "def example():\\n    return True\\n",
                    "tests/test_generated_example.py": "def test_example():\\n    assert True\\n",
                },
                "metadata": {},
            },
        }
