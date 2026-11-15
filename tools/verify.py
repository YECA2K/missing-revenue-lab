"""Maintainer check: prove the starter is broken and the reference passes."""
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import test_pipeline
from lab.pipeline import Pipeline as Starter
from solutions.pipeline import Pipeline as Reference

EXPECTED = {
    "test_late_record_with_equal_timestamp_is_not_lost",
    "test_repeated_order_in_one_delivery_is_counted_once",
    "test_correction_replaces_previous_order_value",
    "test_older_timestamp_new_identity_is_still_loaded",
}


def check(implementation):
    test_pipeline.Pipeline = implementation
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_pipeline.AcceptanceChecks)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    return result, output.getvalue()


def main():
    starter, starter_log = check(Starter)
    failures = {case._testMethodName for case, _ in starter.failures}
    if starter.errors or failures != EXPECTED or starter.testsRun != 8:
        print(starter_log)
        raise SystemExit("Starter behavior differs from the documented incident.")
    print("PASS: starter exposes exactly the four documented failing checks (8 checks run).")
    reference, reference_log = check(Reference)
    if not reference.wasSuccessful() or reference.testsRun != 8:
        print(reference_log)
        raise SystemExit("Reference checks failed.")
    print("PASS: reference implementation passes all 8 acceptance checks.")


if __name__ == "__main__":
    main()
