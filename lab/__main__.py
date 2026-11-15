"""Command line entry point for Missing Revenue Lab."""
import argparse
import contextlib
import io
import json
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description="Investigate three fictional data incidents. No Docker or packages required.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List the incidents")
    sub.add_parser("doctor", help="Check this Python installation")
    for name in ("check", "state", "demo"):
        command = sub.add_parser(name, help={"check": "Run learner acceptance checks", "state": "Export evidence as JSON", "demo": "Print an incident summary"}[name])
        command.add_argument("--case", choices=("revenue", "grain", "timezone"), default="revenue")
        command.add_argument("--solution", action="store_true", help="Use the reference (spoilers)")
    serve = sub.add_parser("serve", help="Open the local investigation dashboard")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--open", action="store_true", help="Open a browser tab")
    args = parser.parse_args(argv)
    if args.command == "serve":
        from lab.server import serve
        return serve(args.port, args.open)
    if args.command == "doctor":
        import sqlite3
        print(f"Python {sys.version.split()[0]} | SQLite {sqlite3.sqlite_version}")
        print("OK: standard-library dependencies available. No Docker, API key or virtualization needed.")
        return 0
    from lab.cases import CASES
    if args.command == "list":
        for slug, case in CASES.items():
            print(f"{case['id']}  {slug:9}  {case['title']}  ({case['minutes']} min)")
        return 0
    from lab.runner import state
    # Keep JSON valid even when a learner adds debugging print statements.
    with contextlib.redirect_stdout(io.StringIO()):
        result = state(args.case, args.solution)
    if args.command == "state":
        print(json.dumps(result, ensure_ascii=True))
        return 0
    print(f"{result['id']} | {result['title']} | {result['mode']}")
    if args.command == "check":
        for check in result["checks"]:
            print(f"{check['status'].upper():5} {check['name']}")
            if check["status"] != "pass":
                print(f"      {check['detail']}")
        print(f"{result['passed']}/{len(result['checks'])} checks passed.")
        return 0 if result["passed"] == len(result["checks"]) else 1
    def money(value):
        return "unavailable" if value is None else f"EUR {value / 100:,.2f}"
    print(f"Expected {money(result['expected_cents'])} | Actual {money(result['actual_cents'])}")
    print(f"Checks: {result['passed']}/{len(result['checks'])}. Edit {result['edit']}.")
    if result["execution_error"]:
        print(result["execution_error"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
