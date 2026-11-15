"""Optional browser QA. Requires Playwright and an installed Edge or Chromium.

Run a local server first, then: python tools/browser_check.py --browser-channel msedge
Screenshots contain fictional lab data only. This script uses a fresh browser profile.
"""
import argparse
import atexit
from pathlib import Path
import sys
import threading
from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--browser-channel", default="msedge")
    parser.add_argument("--start-server", action="store_true", help="Start a temporary loopback server on a free port")
    parser.add_argument("--output", type=Path, default=Path("work/browser-qa"))
    args = parser.parse_args()
    if args.start_server:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from lab.server import make_server
        server = make_server(0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        atexit.register(server.server_close)
        atexit.register(server.shutdown)
        args.url = f"http://127.0.0.1:{server.server_port}"
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.browser_channel, headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url)
        expect(page.locator("#actual-value")).to_have_text("€95,000.00")
        expect(page.locator("#check-count")).to_have_text("4 / 8")
        page.screenshot(path=str(args.output / "dashboard.png"), full_page=True)
        page.locator("#contract-toggle").click()
        expect(page.locator("#contract-content")).to_be_visible()
        page.locator("#contract-toggle").click()
        page.locator("#hint-button").click()
        expect(page.locator("#hint-count")).to_have_text("1 / 4")
        page.locator("#tab-checks").click()
        expect(page.locator(".check.fail")).to_have_count(4)
        page.locator(".check.fail summary").first.click()
        page.screenshot(path=str(args.output / "checks.png"), full_page=True)
        page.locator("#tab-checks").press("ArrowRight")
        expect(page.locator("#view-notes")).to_be_visible()
        page.locator("#notes").fill("QA note: arrival time differs from source update time.")
        page.reload()
        expect(page.locator("#actual-value")).to_have_text("€95,000.00")
        page.locator("#tab-notes").click()
        expect(page.locator("#notes")).to_have_value("QA note: arrival time differs from source update time.")
        with page.expect_download() as download:
            page.locator("#notes-export").click()
        assert download.value.suggested_filename == "inc-001-investigation.md"
        page.locator("#notes").fill("")
        page.locator("#tab-evidence").click()
        page.locator("#reference-button").click()
        expect(page.locator("#reference-dialog")).to_be_visible()
        page.locator("#cancel-reference").click()
        expect(page.locator("#actual-value")).to_have_text("€95,000.00")
        page.locator("#reference-button").click()
        page.locator("#confirm-reference").click()
        expect(page.locator("#actual-value")).to_have_text("€100,000.00")
        expect(page.locator("#check-count")).to_have_text("8 / 8")
        page.screenshot(path=str(args.output / "reference.png"), full_page=True)
        for case, title, actual, checks in [("grain", "The refund multiplier.", "€410.00", "4 / 8"),
                                             ("timezone", "The midnight shift.", "€250.00", "2 / 11")]:
            page.locator(f'a[data-case="{case}"]').click()
            expect(page.locator("#case-title")).to_have_text(title)
            expect(page.locator("#actual-value")).to_have_text(actual)
            expect(page.locator("#check-count")).to_have_text(checks)
            page.screenshot(path=str(args.output / f"{case}.png"), full_page=True)
            page.locator("#reference-button").click()
            page.locator("#confirm-reference").click()
            expect(page.locator("#gap-value")).to_have_text("€0.00")
        page.locator('a[data-case="revenue"]').click()
        expect(page.locator("#actual-value")).to_have_text("€95,000.00")
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Horizontal overflow on mobile"
        page.screenshot(path=str(args.output / "mobile.png"), full_page=True)
        page.locator("#quick-guide").click()
        expect(page.locator("#guide-dialog")).to_be_visible()
        page.locator("#watch-video-mobile").click()
        expect(page.locator("#video-dialog")).to_be_visible()
        page.locator("#walkthrough-video").evaluate("video => { video.muted=true; video.load(); }")
        duration = page.locator("#walkthrough-video").evaluate("""video => new Promise((resolve, reject) => {
            if (Number.isFinite(video.duration)) return resolve(video.duration);
            const timer = setTimeout(() => reject(new Error('Video metadata timeout')), 10000);
            video.addEventListener('loadedmetadata', () => { clearTimeout(timer); resolve(video.duration); }, {once:true});
            video.addEventListener('error', () => { clearTimeout(timer); reject(new Error('Video failed to load')); }, {once:true});
        })""")
        assert duration > 260
        page.locator("#walkthrough-video").evaluate("video => video.play()")
        page.locator("#close-video").click()
        assert page.locator("#walkthrough-video").evaluate("video => video.paused")
        for width in [320, 768, 1024, 1280]:
            page.set_viewport_size({"width": width, "height": 900})
            fits = page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if not fits:
                detail = page.evaluate("""() => [...document.querySelectorAll('body *')].map(el => ({
                    tag:el.tagName, id:el.id, cls:el.className.baseVal ?? el.className,
                    right:Math.round(el.getBoundingClientRect().right)
                })).filter(el => el.right > innerWidth && ['TD','TH','TR','TABLE','TBODY','THEAD'].indexOf(el.tag) < 0).slice(0,20)""")
                page.screenshot(path=str(args.output / f"overflow-{width}.png"), full_page=True)
                raise AssertionError(f"Horizontal overflow at {width}px: {detail}")
        assert not errors, errors
        browser.close()
    print("PASS: responsive layout, navigation, evidence, checks, hints, reference gate, notes persistence, export, video playback and console.")


if __name__ == "__main__":
    main()
