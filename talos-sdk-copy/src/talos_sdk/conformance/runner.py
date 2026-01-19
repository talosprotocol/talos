import json
import os
import time
from typing import Any

from .handlers import BaseHandler, get_handler_for_file
from .reports import JUnitReport

# Tuple: (test_id, status, message, duration)
TestResult = tuple[str, str, str | None, float]


def run_conformance(vectors_path: str, report_path: str | None = None) -> bool:
    with open(vectors_path) as f:
        data = json.load(f)

    # If it is a release set (list of filenames), recurse
    if "version" in data and "vectors" in data and isinstance(data["vectors"], list):
        if len(data["vectors"]) > 0 and isinstance(data["vectors"][0], str):
            return _run_release_set(vectors_path, data)

    filename = os.path.basename(vectors_path)
    handler = get_handler_for_file(filename)
    if not handler:
        return True  # Skip files without handlers

    results, total, failures, errors, duration = _process_conformance_data(
        filename, data, handler
    )

    if report_path:
        suite_name = f"Conformance.{filename.replace('.json', '')}"
        report = JUnitReport()
        _write_report(
            report, suite_name, results, total, failures, errors, duration, report_path
        )

    _print_results(filename, total, failures, errors, duration)
    return failures == 0 and errors == 0


def _process_conformance_data(
    filename: str, data: dict[str, Any], handler: BaseHandler
) -> tuple[list[TestResult], int, int, int, float]:
    total = 0
    failures = 0
    errors = 0
    results: list[TestResult] = []
    start_time = time.time()

    if "steps" in data:
        res = _run_trace_file(filename, data, handler)
        results.append(res)
        total += 1
        if res[1] == "failure":
            failures += 1
        elif res[1] == "error":
            errors += 1
    elif "vectors" in data or "test_cases" in data:
        v_results, v_total, v_failures, v_errors = _run_multi_vector_file(data, handler)
        results.extend(v_results)
        total += v_total
        failures += v_failures
        errors += v_errors
    else:
        res = _run_single_vector_file(filename, data, handler)
        results.append(res)
        total += 1
        if res[1] == "failure":
            failures += 1
        elif res[1] == "error":
            errors += 1

    duration = time.time() - start_time
    return results, total, failures, errors, duration


def _run_release_set(vectors_path: str, data: dict[str, Any]) -> bool:
    base_dir = os.path.dirname(vectors_path)
    all_success = True
    for sub_vector in data["vectors"]:
        sub_path = os.path.join(base_dir, sub_vector)
        success = run_conformance(sub_path, None)
        if not success:
            all_success = False
    return all_success


def _run_trace_file(
    filename: str, data: dict[str, Any], handler: BaseHandler
) -> TestResult:
    t0 = time.time()
    try:
        handler.run_trace(data)
        if "expected_error" in data:
            return (
                filename,
                "failure",
                "Expected error but trace succeeded",
                time.time() - t0,
            )
        return (filename, "passed", None, time.time() - t0)
    except AssertionError as e:
        return (filename, "failure", str(e), time.time() - t0)
    except Exception as e:
        if "expected_error" in data:
            expected = data["expected_error"]
            msg = str(e)
            if (
                expected.get("message_contains")
                and expected["message_contains"] not in msg
            ):
                return (
                    filename,
                    "failure",
                    f"Error mismatch. Got: {msg}",
                    time.time() - t0,
                )
            return (filename, "passed", None, time.time() - t0)
        return (filename, "error", str(e), time.time() - t0)


def _run_multi_vector_file(
    data: dict[str, Any], handler: BaseHandler
) -> tuple[list[TestResult], int, int, int]:
    vectors = data.get("vectors", data.get("test_cases", []))
    results: list[TestResult] = []
    total = 0
    failures = 0
    errors = 0
    for vec in vectors:
        total += 1
        t0 = time.time()
        test_id = vec.get("test_id", vec.get("id", "unknown"))
        try:
            handler.run_vector(vec)
            results.append((test_id, "passed", None, time.time() - t0))
        except AssertionError as e:
            failures += 1
            results.append((test_id, "failure", str(e), time.time() - t0))
        except Exception as e:
            errors += 1
            results.append((test_id, "error", str(e), time.time() - t0))
    return results, total, failures, errors


def _run_single_vector_file(
    filename: str, data: dict[str, Any], handler: BaseHandler
) -> TestResult:
    t0 = time.time()
    try:
        if "expected_error" in data:
            handler.run_negative(data)
        else:
            handler.run_vector(data)
        return (data.get("test_id", filename), "passed", None, time.time() - t0)
    except AssertionError as e:
        return (data.get("test_id", filename), "failure", str(e), time.time() - t0)
    except Exception as e:
        return (data.get("test_id", filename), "error", str(e), time.time() - t0)


def _write_report(
    report: JUnitReport,
    suite_name: str,
    results: list[TestResult],
    total: int,
    failures: int,
    errors: int,
    duration: float,
    report_path: str,
) -> None:
    suite = report.add_testsuite(suite_name, total, failures, errors, duration)
    for test_id, status, message, d in results:
        case = report.add_testcase(suite, test_id, suite_name, d)
        if status == "failure":
            report.add_failure(case, message or "Unknown failure")
        elif status == "error":
            report.add_error(case, message or "Unknown error")
    report.write(report_path)
    print(f"Report written to {report_path}")


def _print_results(
    filename: str, total: int, failures: int, errors: int, duration: float
) -> None:
    print(f"Ran {total} tests in {duration:.4f}s")
    if failures or errors:
        print(f"FAILED (failures={failures}, errors={errors})")
    else:
        print("OK")
    if (failures or errors) and total > 0:
        print(f"\nFailures in {filename}:")
