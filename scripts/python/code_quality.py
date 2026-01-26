#!/usr/bin/env python3
"""
Python Code Quality Analysis Script

Following Real Python's Python Code Quality guide:
https://realpython.com/python-code-quality/

This script runs comprehensive code quality checks:
1. Linting (ruff) - Style, errors, best practices
2. Type checking (mypy) - Static type analysis
3. Security scanning (bandit) - Vulnerability detection
4. Complexity analysis (radon) - Cyclomatic complexity
5. Test coverage (pytest-cov) - Code coverage

Usage:
    python scripts/code_quality.py [--full]
"""

import subprocess
import sys
import os


def run_cmd(command: list[str], check: bool = False) -> tuple[int, str]:
    """Run a command and return (exit_code, output)."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return result.returncode, result.stdout + result.stderr


def print_header(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()


def check_linting() -> bool:
    """Run ruff linter."""
    print_header("1. LINTING (ruff)")
    
    code, output = run_cmd(["ruff", "check", "src/", "tests/", "--statistics"])
    
    if code == 0:
        print("✅ All linting checks passed")
        return True
    else:
        print("❌ Linting issues found:")
        print(output)
        return False


def check_types() -> bool:
    """Run mypy type checker on core modules."""
    print_header("2. TYPE CHECKING (mypy)")
    
    core_files = [
        "src/core/capability.py",
        "src/core/gateway.py",
        "src/core/rate_limiter.py",
        "src/core/key_security.py",
        "src/core/audit_plane.py",
    ]
    
    # Check which files exist
    existing = [f for f in core_files if os.path.exists(f)]
    
    if not existing:
        print("⚠️ No core files found to type check")
        return True
    
    code, output = run_cmd(["mypy", "--ignore-missing-imports"] + existing)
    
    if code == 0 or "no issues found" in output.lower():
        print(f"✅ No type issues in {len(existing)} core files")
        return True
    else:
        print("❌ Type issues found:")
        print(output)
        return False


def check_security() -> bool:
    """Run bandit security scanner."""
    print_header("3. SECURITY SCANNING (bandit)")
    
    code, output = run_cmd(["bandit", "-r", "src/", "-f", "txt", "-q"])
    
    # Count issues by severity
    high_issues = output.count("Severity: High")
    medium_issues = output.count("Severity: Medium")
    low_issues = output.count("Severity: Low")
    
    print(f"  High severity:   {high_issues}")
    print(f"  Medium severity: {medium_issues}")
    print(f"  Low severity:    {low_issues}")
    print()
    
    if high_issues > 0:
        print("❌ Security scan found high-severity issues:")
        print(output)
        return False
    elif medium_issues > 0:
        print("⚠️ Medium-severity issues found (review recommended)")
        return True
    else:
        print("✅ No high/medium security issues")
        return True


def check_complexity() -> bool:
    """Run radon complexity analysis."""
    print_header("4. COMPLEXITY ANALYSIS (radon)")
    
    code, output = run_cmd(["radon", "cc", "src/", "-a", "-s", "-nc"])
    
    # Count high-complexity functions
    high_cc = len([line for line in output.split("\n") if " - C " in line or " - D " in line or " - F " in line])
    
    # Get average
    avg_line = [line for line in output.split("\n") if "Average complexity:" in line]
    avg_cc = avg_line[0] if avg_line else "Unknown"
    
    print(f"  High complexity (C+): {high_cc} functions")
    print(f"  {avg_cc}")
    print()
    
    if high_cc > 20:
        print("❌ Too many high-complexity functions")
        return False
    else:
        print("✅ Complexity within acceptable limits")
        return True


def check_tests() -> bool:
    """Run pytest with coverage."""
    print_header("5. TEST COVERAGE (pytest)")
    
    code, output = run_cmd(["pytest", "tests/", "-q", "--cov=src", "--cov-report=term-missing"])
    
    # Parse results
    lines = output.split("\n")
    
    # Find test count
    for line in lines:
        if "passed" in line:
            print(f"  {line.strip()}")
            break
    
    # Find coverage
    for line in lines:
        if "TOTAL" in line:
            parts = line.split()
            if len(parts) >= 4:
                coverage = parts[3]
                print(f"  Coverage: {coverage}")
                break
    
    print()
    
    if code == 0:
        print("✅ All tests passed")
        return True
    else:
        print("❌ Test failures detected")
        return False


def main() -> int:
    """Run all code quality checks."""
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           PYTHON CODE QUALITY ANALYSIS                     ║")
    print("║   Following Real Python's Code Quality Guide               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    results = {}
    
    # Run all checks
    results["linting"] = check_linting()
    results["types"] = check_types()
    results["security"] = check_security()
    results["complexity"] = check_complexity()
    results["tests"] = check_tests()
    
    # Summary
    print_header("SUMMARY")
    
    all_passed = all(results.values())
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check.capitalize()}")
    
    print()
    
    if all_passed:
        print("🎉 ALL CODE QUALITY CHECKS PASSED")
        return 0
    else:
        print("⚠️ Some checks failed - review above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
