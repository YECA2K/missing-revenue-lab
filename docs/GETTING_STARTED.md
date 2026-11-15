# Start your first investigation

## 1. Get the project

Install Python 3.11 or newer. Git is optional if you download the repository ZIP instead.
Use your regular user account; no administrator rights, Docker, virtualization or database
server are required. Python must have its standard SQLite module.

```sh
git clone https://github.com/YECA2K/missing-revenue-lab.git
cd missing-revenue-lab
python -m lab doctor
python -m lab serve --open
```

If your command is `py` or `python3`, use that consistently instead of `python`.
Windows users can also double-click `start-lab.cmd` after extracting the whole project.

The dashboard listens on **http://127.0.0.1:8765**. It works without internet after downloading.
Leave the terminal running while using it. Stop it with **Ctrl+C**. If the port is occupied:

```sh
python -m lab serve --port 8766 --open
```

The dashboard is a local developer tool, not an internet-hosted service. It runs your learner
Python code in a fresh process on every refresh. The 10-second timeout is a convenience,
not a security sandbox. Only run project code you trust.

## 2. Investigate

Choose one of three incidents in the sidebar. Inspect its source contract and tables, then
record a hypothesis in **Your notes**. Reveal hints progressively if needed.

| Incident | Edit | Initial checks |
| --- | --- | --- |
| Missing revenue | `lab/pipeline.py` | 4/8 pass |
| Refund multiplier | `lab/refunds.py` | 4/8 pass |
| Midnight shift | `lab/daily_revenue.py` | 2/11 pass |

Intentional failures are the exercises. Application errors (for example, a syntax error) are
different: the dashboard shows an error banner. Fix the Python code before re-evaluating.

## 3. Repair and prove

Open the indicated file in your preferred code editor. Edit and save; the dashboard itself
does not modify source files. Click **Run checks** (or press **R** outside a text field).
Its next evaluation imports your latest saved code in a fresh process.

All checks passing is the target, not just a zero discrepancy on the headline example.
Do not modify tests or fixtures to make the numbers look right.

## 4. Compare and explain

The **Reference** view is spoiler-gated and runs the included solution; it leaves your learner
file unchanged. Choose **Your code** to return to your implementation. The walkthrough video
and `solutions/` folder also contain spoilers.

Notes are saved in your browser's local storage, per incident, not in GitHub or a cloud account.
Different browser profiles or ports may have separate storage. Export Markdown before clearing
browser data. Private browsing or disabled storage may prevent persistence.

## Terminal workflow

```sh
python -m lab list
python -m lab demo --case revenue
python -m lab check --case revenue
python -m lab check --case grain
python -m lab check --case timezone
python -m lab check --case revenue --solution
python -m lab state --case revenue
```

`check` exits with code 1 while learner checks fail. `state` prints JSON evidence. The original
`python -m lab.demo` command still works for INC-001.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `python` not found | Use `py` on Windows or `python3` on macOS/Linux; otherwise install Python. |
| `No module named lab` | Open the terminal in the extracted repository root, beside `README.md`. |
| Four failed checks on INC-001 | Expected before the repair. Start investigating. |
| Browser shows unavailable results | Check the error banner, save valid Python code, then rerun. |
| Browser cannot connect | Keep `python -m lab serve` running; use the printed localhost URL. |
| Checks time out | Inspect for loops; run the CLI command for more direct feedback. |
| `ModuleNotFoundError: sqlite3` | Use a Python distribution compiled with SQLite support. |
| Reference passes but Your code fails | The reference does not edit your workspace. Implement your own repair. |

Issue reports should include Python version, operating system, command and error text.
Do not upload employer, customer or personal records.
