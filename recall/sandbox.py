from __future__ import annotations

"""Safe code execution sandbox for running student code against test cases."""

import os
import subprocess
import sys
import tempfile
from typing import Any

MAX_OUTPUT_CHARS: int = 10_000
DEFAULT_TIMEOUT: int = 5
SUPPORTED_LANGUAGES: set[str] = {"python", "py", "python3"}

__all__ = ["run_code", "run_tests"]


def run_code(
    code: str,
    language: str = "python",
    timeout: int = DEFAULT_TIMEOUT,
    input_data: str | None = None,
) -> dict[str, Any]:
    """Execute source code in a temporary file sandbox via subprocess.

    Args:
        code: The source code string to execute.
        language: Programming language (currently only Python is supported).
        timeout: Maximum execution duration in seconds. Defaults to 5.
        input_data: Optional string input passed to stdin.

    Returns:
        dict with keys:
            stdout: Captured standard output (limited to 10,000 characters).
            stderr: Captured standard error (limited to 10,000 characters).
            returncode: Subprocess exit code (0 on success, -1 on timeout/unsupported).
            timed_out: Boolean indicating if execution timed out.
            error: Error message string if execution failed, otherwise None.
    """
    lang_normalized = (language or "").strip().lower()
    if lang_normalized not in SUPPORTED_LANGUAGES:
        return {
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "timed_out": False,
            "error": "Only Python execution is supported currently",
        }

    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write(code)
            temp_file.flush()

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            [sys.executable, temp_path],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        stdout = (result.stdout or "")[:MAX_OUTPUT_CHARS]
        stderr = (result.stderr or "")[:MAX_OUTPUT_CHARS]
        error_msg = None
        if result.returncode != 0:
            error_msg = stderr.strip() or f"Process exited with code {result.returncode}"

        return {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": result.returncode,
            "timed_out": False,
            "error": error_msg,
        }
    except subprocess.TimeoutExpired as exc:
        raw_stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        raw_stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "stdout": (raw_stdout or "")[:MAX_OUTPUT_CHARS],
            "stderr": (raw_stderr or "")[:MAX_OUTPUT_CHARS],
            "returncode": -1,
            "timed_out": True,
            "error": f"Execution timed out after {timeout} seconds",
        }
    except Exception as exc:
        return {
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "timed_out": False,
            "error": str(exc),
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def run_tests(
    code: str,
    test_cases: list[dict[str, Any]],
    language: str = "python",
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Execute code against test cases with stdin input and stdout comparison.

    Args:
        code: The student's code to test.
        test_cases: List of test case dicts, each with 'input' and 'expected_output'.
        language: Programming language to run (defaults to 'python').
        timeout: Execution timeout per test case in seconds (defaults to 5).

    Returns:
        dict with keys:
            passed: Number of passed test cases.
            failed: Number of failed test cases.
            total: Total number of test cases.
            results: List of dicts, each containing:
                input: Test case input string.
                expected: Expected output string.
                actual: Actual output string.
                passed: Boolean indicating if the test case passed.
                error: Error message string or None.
    """
    results: list[dict[str, Any]] = []
    passed_count = 0

    cases = test_cases or []
    for tc in cases:
        tc_input = str(tc.get("input", "") if tc.get("input") is not None else "")
        raw_expected = tc.get("expected_output")
        if raw_expected is None:
            raw_expected = tc.get("expected", "")
        expected = str(raw_expected).strip()

        exec_res = run_code(
            code=code,
            language=language,
            timeout=timeout,
            input_data=tc_input,
        )

        actual = exec_res["stdout"].strip()
        timed_out = exec_res["timed_out"]
        returncode = exec_res["returncode"]
        err = exec_res["error"]

        is_passed = (
            not timed_out
            and returncode == 0
            and actual == expected
        )

        if is_passed:
            passed_count += 1
            case_error = None
        else:
            if timed_out:
                case_error = err or f"Execution timed out after {timeout} seconds"
            elif returncode != 0:
                case_error = err or exec_res.get("stderr", "").strip() or f"Process exited with code {returncode}"
            elif err:
                case_error = err
            else:
                case_error = None

        results.append({
            "input": tc_input,
            "expected": expected,
            "actual": actual,
            "passed": is_passed,
            "error": case_error,
        })

    total = len(cases)
    failed_count = total - passed_count

    return {
        "passed": passed_count,
        "failed": failed_count,
        "total": total,
        "results": results,
    }
