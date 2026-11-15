"""Verify references; --starter also checks the original teaching failures."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab.cases import CASES
from lab.runner import run_checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starter", action="store_true", help="Require the pristine starter's documented failures")
    args = parser.parse_args()
    failed = False
    for slug, case in CASES.items():
        reference = run_checks(slug, solution=True)
        errors = [check for check in reference if check["status"] != "pass"]
        expected_count = {"revenue": 8, "grain": 8, "timezone": 11}[slug]
        if len(reference) != expected_count:
            print(f"FAIL {case['id']}: expected {expected_count} checks, found {len(reference)}")
            failed = True
        print(f"{'FAIL' if errors else 'PASS'} {case['id']} reference: {len(reference)-len(errors)}/{len(reference)} checks")
        if errors:
            failed = True
            for check in errors:
                print(check)
        if args.starter:
            starter = run_checks(slug)
            failures = {check["name"] for check in starter if check["status"] == "fail"}
            valid = failures == set(case["expected_failures"]) and not any(check["status"] == "error" for check in starter)
            print(f"{'PASS' if valid else 'FAIL'} {case['id']} starter: {len(failures)} expected teaching failures")
            failed |= not valid
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
