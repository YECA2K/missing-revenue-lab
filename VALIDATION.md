# Validation

Validated locally on Windows on November 16, 2026, with Python 3.15.2 and SQLite 3.53.4.
Browser QA used an isolated headless Microsoft Edge profile through Playwright 1.65.2.

## Incident checks

`python tools/verify.py --starter` verifies all references and the pristine teaching failures:

| Incident | Reference | Original learner code |
| --- | --- | --- |
| INC-001 | 8 / 8 pass | Exactly 4 expected assertion failures |
| INC-002 | 8 / 8 pass | Exactly 4 expected assertion failures |
| INC-003 | 11 / 11 pass | Exactly 9 expected assertion failures |

Reference control totals reconcile at EUR 100,000, EUR 130 and EUR 300 respectively.
The original code reports EUR 95,000, EUR 410 and EUR 250. Fresh in-memory data is used each time.

## Application checks

`python -m unittest tests.test_system -v`: **14 checks passed**. They cover reference behavior,
out-of-order replay invariance, CLI JSON and exit status, HTTP assets and evidence evaluation,
invalid paths, unexpected hosts/origins, worker errors/timeouts and MP4 byte ranges for seeking.
An isolated project-copy test also verifies that a saved learner repair is picked up by the next worker.
Resource-warning checks passed after fixing SQLite connection lifetimes.

`tools/browser_check.py --start-server`: passed real-browser interactions for incident navigation,
evidence tables, expandable checks, hints, spoiler confirmation, reference totals, notes persistence,
Markdown download, help and video playback/pause. No application JavaScript errors were observed.
Layout checks found no page-level horizontal overflow at 320, 390, 768, 1024, 1280 and 1600 pixels.
Desktop/mobile screenshots were visually inspected. These checks are not a formal accessibility audit.

## Video

The generated walkthrough is 1920×1080 H.264/AAC MP4, approximately 4 minutes 29 seconds.
It contains synthetic narration, burned-in captions, actual dashboard crops and annotated repair
explanations. The full file decoded successfully with FFmpeg; representative frames were visually
inspected. Playback and metadata loading were verified in the local dashboard. Source narration,
SRT captions, chapters and reproducible asset-production tools are included.

## CI

The workflow verifies references and application behavior on Windows and Linux with Python
3.11–3.15, and runs the browser suite in Chromium. Consult the
[actual workflow results](https://github.com/YECA2K/missing-revenue-lab/actions/workflows/verify.yml)
for the commit being used. A workflow configuration alone is not proof of a completed run.

## Limits

No macOS-native browser or screen-reader audit has been performed. The local HTTP server runs
trusted learner code and is not an internet service or an execution sandbox. Fixed-offset timezone
checks do not exercise DST. The fictional accounting examples are teaching metrics, not financial
advice or production controls. No performance, demand, revenue or learning outcomes were measured.
