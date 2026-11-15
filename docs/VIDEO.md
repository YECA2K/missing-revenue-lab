# Solution walkthrough — spoilers

Generated 1080p video with synthetic English narration, burned-in captions and actual dashboard captures.
Approximately 4 minutes 29 seconds. The video explains all three reference repairs; it does not modify learner files.

[Download the video](media/solution-walkthrough.mp4) · [SRT captions](media/solution-walkthrough.srt)

## Chapters

- 00:00 · Green jobs. Wrong numbers.
- 00:23 · One command. Three investigations.
- 00:47 · Same timestamp. Different arrival.
- 01:12 · Identity first. Newer versions win.
- 01:42 · Prove the repair, not just the total.
- 02:10 · Two items × two refunds = four rows.
- 02:36 · Aggregate before you join.
- 03:03 · UTC midnight is not business midnight.
- 03:30 · Parse. Convert. Then group.
- 04:00 · Follow the evidence. Ship the fix.

## Transcript

### 00:00 · Green jobs. Wrong numbers.

A pipeline can finish successfully and still produce the wrong numbers. In Missing Revenue Lab, the source reports one hundred thousand euros, but the warehouse reports ninety five thousand. This fictional incident gives you the code, evidence, and tests to investigate the missing five thousand euros.

### 00:23 · One command. Three investigations.

Clone the repository and run python dash m lab serve dash dash open. The dashboard runs on your own computer with Python and SQLite. No Docker, cloud account, or API key is required. Read the source contract, inspect the evidence, and edit the indicated Python file in your editor.

### 00:47 · Same timestamp. Different arrival.

The first delivery advances the checkpoint to ten o'clock. A different order arrives in the second delivery with that same source timestamp. The loader selects only timestamps strictly greater than the checkpoint, so it silently excludes the new order. Source update time does not tell you which identities have already arrived.

### 01:12 · Identity first. Newer versions win.

Changing greater than to greater than or equal is not enough. It can replay orders, and it still misses arbitrarily late records. Our source delivers complete extracts, so the reference processes every record. Order identity is a primary key. An upsert replaces an existing order only with a newer version. Duplicate deliveries no longer create revenue.

### 01:42 · Prove the repair, not just the total.

The reference now reports one hundred thousand euros, and all eight acceptance checks pass. The checks also exercise duplicate rows, repeated deliveries, corrected amounts, stale versions, and older new identities. Use the reference view to inspect the result. It does not replace your learner code. Your own repair must pass independently.

### 02:10 · Two items × two refunds = four rows.

The second incident is a reporting grain problem. One hundred and fifty euros of orders minus twenty euros of refunds should produce one hundred and thirty euros. But joining two items and two refunds creates four rows for one order. The query repeats the order amount and reports four hundred and ten euros overall.

### 02:36 · Aggregate before you join.

Aggregate refunds to one row per order before joining them to the orders table. Then sum each order amount minus its refund total. The item table is unnecessary for this metric. Do not use sum distinct on monetary values. Two legitimate orders or refunds can have exactly the same amount. All eight checks now pass.

### 03:03 · UTC midnight is not business midnight.

The third incident uses a fixed business offset of UTC plus two hours. An order at ten thirty PM UTC on June fourteenth belongs to June fifteenth locally. Another at ten fifteen PM UTC on June fifteenth belongs to the next day. Slicing the timestamp's date reports two hundred and fifty euros instead of three hundred.

### 03:30 · Parse. Convert. Then group.

Parse a timezone aware datetime, convert it to the business offset, and compare its local date. Reject missing or invalid timezones instead of guessing. All eleven checks pass, including midnight boundaries and negative offsets. This exercise deliberately uses a fixed offset. Real regional calendars with daylight saving require named timezones and a timezone database.

### 04:00 · Follow the evidence. Ship the fix.

Now try the incidents yourself. Write down your hypothesis, repair the learner files, and rerun the checks. Export your investigation notes and explain the remaining limitations. Missing Revenue Lab is published by YECA2K with Codex assistance. The data is synthetic, the challenges are free, and the reference solutions are included.

## Rebuild the assets

The lab itself needs no external packages. Asset production is optional development work.
Install `requirements-media.txt` in an isolated environment. Capture screenshots with
`python tools/browser_check.py --start-server --output docs/media`. On Windows, use `tools/narrate.ps1`
with `docs/video-script.json` and a project-local work directory to generate WAV files.
It uses the installed Microsoft Hazel Desktop voice; choose another installed voice if needed.
Then run `python tools/render_video.py --work PATH_TO_WAV_DIRECTORY`.
The renderer uses Pillow and FFmpeg via imageio-ffmpeg; it makes no cloud API requests.
Keep narration, evidence, code and captions in sync when editing.
