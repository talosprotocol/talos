import argparse
import sys

from .runner import run_conformance


def main() -> None:
    parser = argparse.ArgumentParser(description="Talos SDK Conformance Harness")
    parser.add_argument(
        "--vectors", required=True, help="Path to test vector JSON file"
    )
    parser.add_argument("--report", help="Path to write JUnit XML report")

    args = parser.parse_args()

    try:
        success = run_conformance(args.vectors, args.report)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error handling vectors: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
