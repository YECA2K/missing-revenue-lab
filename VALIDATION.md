# Validation

Local verification performed on Windows with Python 3.15.2 and SQLite 3.53.4.

- `python tools/verify.py`: eight checks run against each implementation. The starter
  has exactly four expected assertion failures and no errors; the reference passes all eight.
- `python -m lab.demo`: source EUR 100,000.00; warehouse EUR 95,000.00; gap EUR 5,000.00.
- `python -m lab.demo --solution`: source and warehouse EUR 100,000.00; gap EUR 0.00.

The GitHub Actions workflow additionally runs verification and both demos on Windows and
Linux with Python 3.11, 3.12, 3.13 and 3.14. Its actual results are available in the repository's
Actions tab. A workflow configuration is not evidence of a completed run.

The fixture totals and currency are fictional. No performance, market demand or learning-outcome
claims have been measured. No external data or API calls are required by the Python code.
