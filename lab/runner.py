"""Execute independent acceptance suites and collect inspectable evidence."""
import importlib
import sqlite3
import unittest
from contextlib import closing
from lab.cases import CASES
from lab.fixtures import daily_orders, refund_database, snapshots


class Result(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.checks = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.checks.append({"name": test._testMethodName, "status": "pass", "detail": "Acceptance check passed."})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.checks.append({"name": test._testMethodName, "status": "fail", "detail": str(err[1])})

    def addError(self, test, err):
        super().addError(test, err)
        self.checks.append({"name": test._testMethodName, "status": "error", "detail": f"{err[0].__name__}: {err[1]}"})


def implementation(case, solution=False):
    module = importlib.import_module(f"{'solutions' if solution else 'lab'}.{case['implementation']}")
    return getattr(module, case["symbol"])


def run_checks(slug, solution=False):
    case = CASES[slug]
    tests = importlib.import_module(case["test_module"])
    original = getattr(tests, case["symbol"])
    try:
        setattr(tests, case["symbol"], implementation(case, solution))
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(tests.AcceptanceChecks)
        result = Result()
        suite.run(result)
        return result.checks
    finally:
        setattr(tests, case["symbol"], original)


def evidence(slug, solution=False):
    case = CASES[slug]
    fn = implementation(case, solution)
    if slug == "revenue":
        first, second = snapshots()
        with closing(sqlite3.connect(":memory:")) as db:
            pipeline = fn(db)
            runs = []
            for number, rows in enumerate((first, second), 1):
                written = pipeline.ingest(rows)
                runs.append({"delivery": number, "source_rows": len(rows), "written_rows": written,
                             "warehouse_cents": pipeline.revenue_cents()})
            actual = pipeline.revenue_cents()
            warehouse = [dict(zip(("order_id", "amount_cents", "updated_at"), row)) for row in
                         db.execute("SELECT order_id, amount_cents, updated_at FROM orders ORDER BY order_id")]
        return actual, [{"name": "Source · latest complete extract", "rows": second},
                        {"name": "Warehouse · after both deliveries", "rows": warehouse},
                        {"name": "Load history", "rows": runs}]
    if slug == "grain":
        with closing(sqlite3.connect(":memory:")) as db:
            db.row_factory = sqlite3.Row
            refund_database(db)
            actual = fn(db)
            tables = [{"name": name.replace("_", " ").title(), "rows": [dict(row) for row in db.execute(f"SELECT * FROM {name}")]}
                      for name in ("orders", "order_items", "refunds")]
            joined = db.execute("""SELECT o.order_id, o.amount_cents AS order_cents, i.item_id,
                r.refund_id, r.amount_cents AS refund_cents FROM orders o
                LEFT JOIN order_items i ON i.order_id=o.order_id
                LEFT JOIN refunds r ON r.order_id=o.order_id ORDER BY o.order_id,i.item_id,r.refund_id""")
            tables.append({"name": "Original join · inspect its grain", "rows": [dict(row) for row in joined]})
        return actual, tables
    rows = daily_orders()
    return fn(rows, "2026-06-15", 120), [{"name": "Source orders · timestamp as received", "rows": rows}]


def state(slug, solution=False):
    case = CASES[slug]
    result = {key: value for key, value in case.items()
              if key not in {"test_module", "implementation", "symbol", "expected_failures", "solution", "limitation"}}
    result["mode"] = "reference" if solution else "workspace"
    checks = run_checks(slug, solution)
    result["checks"] = checks
    result["passed"] = sum(check["status"] == "pass" for check in checks)
    try:
        actual, tables = evidence(slug, solution)
        result.update(actual_cents=actual, tables=tables, execution_error=None)
    except Exception as error:
        result.update(actual_cents=None, tables=[], execution_error=f"{type(error).__name__}: {error}")
    if solution:
        result.update(solution=case["solution"], limitation=case["limitation"])
    return result
