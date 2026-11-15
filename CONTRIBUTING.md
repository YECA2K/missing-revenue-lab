# Contributing

Bug reports, improved explanations and additional original scenarios are welcome. Keep the
runtime standard-library-only and the dataset synthetic. Do not contribute employer code,
copied proprietary exercises or personal records.

## Two different kinds of tests

Learner acceptance checks intentionally fail before repairs:

```sh
python -m lab check --case revenue
python -m lab check --case grain
python -m lab check --case timezone
```

Maintainer verification must pass:

```sh
python tools/verify.py
python -m unittest tests.test_system -v
```

These validate the references and application. They remain useful on learner forks after repairs.
For a pristine release checkout, `python tools/verify.py --starter` additionally checks the exact
17 intended failures across the three original learner implementations. Do not run that optional
assertion expecting success after fixing the starter.

## Browser checks (optional)

Install Playwright in an isolated development environment, install its Chromium browser, and run:

```sh
python -m pip install playwright==1.65.2
python -m playwright install chromium
python tools/browser_check.py --browser-channel chromium --start-server --output work/browser-qa
```

On a machine with Edge, `--browser-channel msedge` uses a new isolated browser profile.
The browser suite checks desktop/mobile layout, navigation, evidence, acceptance checks,
spoiler gating, note persistence, export, and console errors. No personal browser profile is used.

## Content changes

Keep the incident brief, `lab/cases.py`, acceptance checks, reference code and video script in sync.
When adding a case, include a source contract, boundary examples, meaningful negative cases,
an explained reference and explicit limitations. Check the actual video as well as its transcript.

## Solution discussions

Use **[SPOILER]** in the issue or pull-request title if it reveals a repair. Avoid posting secrets
or sensitive data in logs. Product support is best-effort; this repository is an educational lab.
