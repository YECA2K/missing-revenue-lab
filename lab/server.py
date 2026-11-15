"""Loopback-only, read-only dashboard for locally trusted learner code."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from pathlib import Path
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlsplit
import webbrowser
from lab.cases import CASES

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(__file__).resolve().parent / "web"
WORKERS = threading.BoundedSemaphore(2)
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8")}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Avoid recording investigation notes or noisy browser requests.
        pass

    def send(self, code, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=True).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if self.headers.get("Host") not in allowed:
            return self.send(403, {"error": "Use this dashboard's localhost address."})
        origin = self.headers.get("Origin")
        if origin and origin not in {f"http://{host}" for host in allowed}:
            return self.send(403, {"error": "Cross-origin requests are not supported."})
        url = urlsplit(self.path)
        if url.path in ASSETS:
            filename, mime = ASSETS[url.path]
            return self.send(200, (WEB / filename).read_bytes(), mime)
        if url.path == "/walkthrough-poster.png":
            return self.send(200, (ROOT / "docs/media/walkthrough-poster.png").read_bytes(), "image/png")
        if url.path == "/walkthrough.mp4":
            return self.send_video()
        if url.path == "/api/catalog":
            return self.send(200, [{key: case[key] for key in
                ("id", "slug", "title", "category", "minutes", "level")} for case in CASES.values()])
        if url.path == "/api/state":
            query = parse_qs(url.query)
            slug = query.get("case", ["revenue"])[0]
            if slug not in CASES:
                return self.send(400, {"error": "Unknown incident."})
            if not WORKERS.acquire(blocking=False):
                return self.send(429, {"error": "Checks are already running. Try again shortly."})
            try:
                command = [sys.executable, "-m", "lab", "state", "--case", slug]
                if query.get("solution", ["0"])[0] == "1":
                    command.append("--solution")
                worker = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                        encoding="utf-8", errors="replace", timeout=10)
                if worker.returncode:
                    return self.send(422, {"error": "Workspace code could not load. Check your Python file for import or syntax errors.",
                                           "detail": worker.stderr[-4000:]})
                return self.send(200, json.loads(worker.stdout))
            except subprocess.TimeoutExpired:
                return self.send(408, {"error": "Checks exceeded 10 seconds. Inspect the workspace for a loop or expensive operation."})
            except (OSError, ValueError):
                return self.send(500, {"error": "Could not evaluate the workspace. See the terminal and run the CLI check."})
            finally:
                WORKERS.release()
        return self.send(404, {"error": "Not found."})

    def send_video(self):
        path = ROOT / "docs/media/solution-walkthrough.mp4"
        if not path.is_file():
            return self.send(404, {"error": "Walkthrough video is missing. Download the full release."})
        size = path.stat().st_size
        start, end, code = 0, size - 1, 200
        requested = self.headers.get("Range")
        if requested:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested)
            valid = match and any(match.groups())
            if valid:
                left, right = match.groups()
                start = int(left) if left else max(0, size - int(right))
                end = min(int(right), size - 1) if left and right else size - 1
                valid = 0 <= start <= end < size and (left or int(right) > 0)
            if not valid:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            code = 206
        self.send_response(code)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("X-Content-Type-Options", "nosniff")
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with path.open("rb") as video:
            video.seek(start)
            remaining = end - start + 1
            try:
                while remaining:
                    chunk = video.read(min(64 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # The browser may cancel a range when seeking or closing.


def make_server(port=8765):
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port=8765, open_browser=False):
    if not 0 <= port <= 65535:
        print("Port must be between 0 and 65535.", file=sys.stderr)
        return 2
    try:
        server = make_server(port)
    except OSError as error:
        print(f"Could not start dashboard: {error}. Try --port 8766.", file=sys.stderr)
        return 2
    address = f"http://127.0.0.1:{server.server_port}"
    print(f"Missing Revenue Lab: {address}\nPress Ctrl+C to stop. Run only code you trust.", flush=True)
    if open_browser:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
    return 0
