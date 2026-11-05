#!/usr/bin/env python3
"""Hutch drawers helper: lets the build tracker open print files straight in Bambu Studio.

Runs on this Mac only (127.0.0.1). The tracker's buttons open a link to it; the helper
  /open?f=projects/...3mf   opens that project from a local copy of the repo
  /labels?d=<data>          builds a Bambu project of label tags and opens it
then closes the browser tab the link opened in. Local files open without Bambu Studio's
"not from a trusted site" prompt.
"""
import base64, json, os, re, subprocess, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 47833
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                       # the git clone this file lives in
LABELS = os.path.join(os.path.dirname(REPO), "labels")
NODE = next((p for p in ("/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node") if os.path.exists(p)), "node")
PROJECT = re.compile(r"^projects/[A-Za-z0-9_\-/]+\.3mf$")
VERSION = "1.1"
_last_pull = 0.0
_pull_lock = threading.Lock()


def pull(force=False):
    """Fast-forward the local copy so new or changed print files show up. At most every 5 minutes."""
    global _last_pull
    with _pull_lock:
        if not force and time.time() - _last_pull < 300:
            return
        _last_pull = time.time()
        subprocess.run(["git", "-C", REPO, "pull", "--ff-only", "-q"], capture_output=True, timeout=60)


def open_in_bambu(path):
    subprocess.run(["open", "-a", "BambuStudio", path], capture_output=True, timeout=30)


CLOSE_TABS = """
on closeIn(appName)
  if application appName is running then
    tell application appName
      repeat with w in windows
        repeat with i from (count of tabs of w) to 1 by -1
          try
            if (URL of tab i of w) starts with "http://127.0.0.1:%d" then close tab i of w
          end try
        end repeat
      end repeat
    end tell
  end if
end closeIn
try
  closeIn("Safari")
end try
try
  closeIn("Google Chrome")
end try
""" % PORT


def close_tabs_soon():
    def run():
        time.sleep(1.2)
        subprocess.run(["osascript", "-e", CLOSE_TABS], capture_output=True, timeout=20)
    threading.Thread(target=run, daemon=True).start()


def page(title, body, ok=True):
    colour = "#3e6a38" if ok else "#a34f17"
    return f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<body style="margin:0;min-height:100vh;display:grid;place-items:center;background:#e9ece6;font:16px -apple-system,BlinkMacSystemFont,sans-serif;color:#151715">
<main style="background:#f8f9f6;border:1px solid #d3d8cf;border-radius:14px;padding:22px 24px;max-width:440px">
<div style="font:12px ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:{colour}">Hutch drawers</div>
<h1 style="font-size:1.25rem;margin:6px 0 8px">{title}</h1><p style="margin:0;color:#5d645c">{body}</p></main>
<script>setTimeout(function(){{window.close()}},400)</script></body>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, html, ctype="text/html; charset=utf-8"):
        data = html.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/ping":
                return self.send(200, json.dumps({"ok": True, "version": VERSION}), "application/json")
            if u.path == "/open":
                f = (q.get("f") or [""])[0]
                if not PROJECT.match(f) or ".." in f:
                    return self.send(400, page("That isn't a hutch drawer project", f, False))
                local = os.path.join(REPO, f)
                if not os.path.exists(local):
                    pull(force=True)
                else:
                    threading.Thread(target=pull, daemon=True).start()
                if not os.path.exists(local):
                    return self.send(404, page("Couldn't find that file", f, False))
                open_in_bambu(local)
                close_tabs_soon()
                return self.send(200, page("Opened in Bambu Studio", os.path.basename(f)))
            if u.path == "/labels":
                raw = (q.get("d") or [""])[0]
                data = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode())
                tags = [{"text": str(t.get("text", ""))[:12], "colour": t.get("colour")}
                        for t in data.get("tags", [])[:300] if t.get("colour") in ("black", "sage")]
                if not tags:
                    return self.send(400, page("No labels to print", "Add some to the label queue first.", False))
                os.makedirs(LABELS, exist_ok=True)
                out = os.path.join(LABELS, time.strftime("hutch_labels_%Y-%m-%d_%H%M%S.3mf"))
                r = subprocess.run([NODE, os.path.join(HERE, "labels.js"), json.dumps({"tags": tags}), out],
                                   capture_output=True, text=True, timeout=120)
                res = json.loads((r.stdout or "{}").strip().splitlines()[-1] or "{}")
                if not res.get("ok"):
                    return self.send(500, page("Couldn't build the labels", res.get("error") or r.stderr[-300:], False))
                open_in_bambu(out)
                close_tabs_soon()
                plates = ", ".join(f"{p['count']} for {p['colour']} fronts" for p in res["plates"])
                return self.send(200, page("Labels opened in Bambu Studio", plates))
            return self.send(404, page("Not found", u.path, False))
        except Exception as e:  # keep running whatever happens
            return self.send(500, page("Something went wrong", str(e), False))


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
