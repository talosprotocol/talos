#!/usr/bin/env python3
"""
Cyclomatic Complexity Analysis for Talos Protocol.

This script analyzes code complexity using radon metrics:
- CC (Cyclomatic Complexity): Number of independent paths
- MI (Maintainability Index): Overall code health
- Halstead: Effort and difficulty metrics

Grades:
- A (1-5): Low complexity, easy to maintain
- B (6-10): Moderate complexity
- C (11-20): High complexity, refactor recommended
- D (21-30): Very high complexity
- F (>30): Extreme complexity, must refactor

Usage:
    python scripts/complexity_analysis.py [--threshold 10]
"""

import subprocess
import sys
import json


def run_radon(command: list[str]) -> str:
    """Run a radon command and return output."""
    result = subprocess.run(
        ["radon"] + command,
        capture_output=True,
        text=True,
        cwd="."
    )
    return result.stdout


def analyze_complexity(threshold: int = 10) -> dict:
    """Analyze cyclomatic complexity of src/ directory."""
    
    print("=" * 60)
    print("  CYCLOMATIC COMPLEXITY ANALYSIS")
    print("=" * 60)
    print()
    
    # Get high-complexity functions
    output = run_radon(["cc", "src/", "-a", "-s", "-nc"])
    
    high_complexity = []
    lines = output.strip().split("\n")
    
    current_file = ""
    for line in lines:
        if line.startswith("src/"):
            current_file = line.strip()
        elif line.strip().startswith(("M ", "F ", "C ")):
            parts = line.strip().split()
            if len(parts) >= 5:
                # Parse: "M 123:4 function_name - C (15)"
                grade = parts[-2]  # C, B, etc.
                try:
                    cc = int(parts[-1].strip("()"))
                    if cc > threshold:
                        high_complexity.append({
                            "file": current_file,
                            "function": parts[2],
                            "line": parts[1],
                            "complexity": cc,
                            "grade": grade,
                        })
                except (ValueError, IndexError):
                    pass
    
    # Sort by complexity
    high_complexity.sort(key=lambda x: x["complexity"], reverse=True)
    
    # Print high complexity functions
    if high_complexity:
        print(f"⚠️  HIGH COMPLEXITY (CC > {threshold}):")
        print()
        print(f"{'File':<40} {'Function':<30} {'CC':>4} {'Grade':>6}")
        print("-" * 82)
        for item in high_complexity:
            file_short = item["file"][-38:] if len(item["file"]) > 38 else item["file"]
            func_short = item["function"][:28] if len(item["function"]) > 28 else item["function"]
            print(f"{file_short:<40} {func_short:<30} {item['complexity']:>4} {item['grade']:>6}")
        print()
    
    # Get summary
    summary_output = run_radon(["cc", "src/", "-a", "-s"])
    summary_lines = summary_output.strip().split("\n")
    
    total_blocks = 0
    avg_complexity = 0.0
    
    for line in summary_lines:
        if "blocks" in line and "analyzed" in line:
            parts = line.split()
            try:
                total_blocks = int(parts[0])
            except (ValueError, IndexError):
                pass
        elif "Average complexity:" in line:
            # Extract: "Average complexity: A (2.51375)"
            try:
                avg_str = line.split("(")[1].rstrip(")")
                avg_complexity = float(avg_str)
            except (ValueError, IndexError):
                pass
    
    # Grade thresholds
    if avg_complexity <= 5:
        overall_grade = "A"
    elif avg_complexity <= 10:
        overall_grade = "B"
    elif avg_complexity <= 20:
        overall_grade = "C"
    else:
        overall_grade = "D"
    
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print()
    print(f"  Total functions analyzed: {total_blocks}")
    print(f"  Average complexity:       {avg_complexity:.2f} ({overall_grade})")
    print(f"  High complexity (>{threshold}):   {len(high_complexity)}")
    print()
    
    # Recommendations
    if high_complexity:
        print("📋 RECOMMENDATIONS:")
        print()
        for item in high_complexity[:5]:
            print(f"  • {item['function']} (CC={item['complexity']})")
            print(f"    Consider breaking into smaller functions")
        print()
    
    return {
        "total_functions": total_blocks,
        "average_complexity": avg_complexity,
        "overall_grade": overall_grade,
        "high_complexity_count": len(high_complexity),
        "high_complexity_functions": high_complexity,
    }


def analyze_maintainability() -> dict:
    """Analyze maintainability index."""
    
    print("=" * 60)
    print("  MAINTAINABILITY INDEX")
    print("=" * 60)
    print()
    
    output = run_radon(["mi", "src/", "-s"])
    
    low_mi = []
    lines = output.strip().split("\n")
    
    for line in lines:
        if " - " in line:
            parts = line.strip().rsplit(" - ", 1)
            if len(parts) == 2:
                file_path = parts[0]
                grade = parts[1].strip()
                
                # MI grades: A (>20), B (10-20), C (<10)
                if grade in ["B", "C"]:
                    low_mi.append({"file": file_path, "grade": grade})
    
    if low_mi:
        print("Files with low maintainability (B or C):")
        for item in low_mi:
            print(f"  {item['grade']}: {item['file']}")
        print()
    else:
        print("✅ All files have good maintainability (grade A)")
        print()
    
    return {"low_maintainability": low_mi}


if __name__ == "__main__":
    threshold = 10
    if len(sys.argv) > 2 and sys.argv[1] == "--threshold":
        try:
            threshold = int(sys.argv[2])
        except ValueError:
            pass
    
    cc_results = analyze_complexity(threshold)
    mi_results = analyze_maintainability()
    
    # Exit with error if too many high-complexity functions
    if cc_results["high_complexity_count"] > 20:
        print("❌ FAIL: Too many high-complexity functions")
        sys.exit(1)
    else:
        print("✅ PASS: Complexity within acceptable limits")
        sys.exit(0)
