"""Run with python -m lab.demo from the repository root."""
import argparse
import sqlite3
from contextlib import closing
from lab.fixtures import snapshots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solution", action="store_true", help="Run the reference implementation (spoilers)")
    args = parser.parse_args()
    if args.solution:
        from solutions.pipeline import Pipeline
    else:
        from lab.pipeline import Pipeline
    with closing(sqlite3.connect(":memory:")) as db:
        pipeline = Pipeline(db)
        first, second = snapshots()
        for name, records in [("Initial source extract delivered at 10:05", first),
                              ("Complete source extract delivered at 10:15", second)]:
            written = pipeline.ingest(records)
            print(f"{name}: wrote {written} rows; revenue EUR {pipeline.revenue_cents() / 100:,.2f}")
        expected = sum(row["amount_cents"] for row in second)
        actual = pipeline.revenue_cents()
        print(f"Source: EUR {expected / 100:,.2f} | Warehouse: EUR {actual / 100:,.2f}")
        print(f"Missing: EUR {(expected - actual) / 100:,.2f}")
        print("Pipeline execution succeeded. Does that mean its data is correct?")


if __name__ == "__main__":
    main()
