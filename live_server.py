#!/usr/bin/env python3
"""LLMOS Live Event Server (pop, 2026-07-25).

Serves a live, scroll-back-able view of what LLMOS is doing RIGHT NOW to the
BrainMonitor page running on the Mac. Two data sources, both under ~/swe/runs:

  - *.log         the per-turn stdout of a run (live today; phase-A source)
  - events.jsonl  structured events emitted by phase_run (phase-B, richer)

Design: byte-offset polling, not a long-lived stream. Short requests survive
the connection resets that killed the chat, and tailing an actively-appended
file by offset is trivial and cheap. ThreadingHTTPServer so a slow poll never
blocks /health or /api/live/runs. CORS * so the Mac page (localhost:9996) can
reach us over the LAN at 192.168.12.232:8899.
"""
import json
import os
import glob
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

SWE = os.path.expanduser("~/swe")
RUNS = os.path.join(SWE, "runs")
PORT = 8899
VERSION = "1.0.0"
DEFAULT_MAX = 65536
HARD_MAX = 1_000_000


def _safe(pathid):
    """Resolve a caller-supplied id to a real path strictly under RUNS."""
    if not pathid:
        return None
    p = os.path.normpath(os.path.join(RUNS, pathid))
    if p != RUNS and not p.startswith(RUNS + os.sep):
        return None
    return p


def _list_runs():
    out = []
    seen = set()
    pats = [os.path.join(RUNS, "*", "*.log"),
            os.path.join(RUNS, "*.log"),
            os.path.join(RUNS, "*", "events.jsonl"),
            os.path.join(RUNS, "*", "*.events.jsonl")]
    for pat in pats:
        for fp in glob.glob(pat):
            if fp in seen or not os.path.isfile(fp):
                continue
            seen.add(fp)
            rel = os.path.relpath(fp, RUNS)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            kind = "events" if fp.endswith(".jsonl") else "log"
            out.append({"id": rel, "kind": kind, "size": st.st_size,
                        "mtime": st.st_mtime, "label": rel})
    out.sort(key=lambda r: r["mtime"], reverse=True)
    return out


class H(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8", "replace")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *a):
        pass  # keep the server quiet; it has one job

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/health":
            return self._send({"ok": True, "service": "llmos-live",
                               "version": VERSION, "runs_dir": RUNS})
        if u.path in ("/", "/api/live/runs"):
            return self._send({"runs": _list_runs()})
        if u.path == "/api/live/tail":
            return self._tail(q)
        return self._send({"error": "unknown endpoint",
                           "endpoints": ["/health", "/api/live/runs",
                                         "/api/live/tail?path&offset&max"]}, 404)

    def _tail(self, q):
        pathid = (q.get("path") or [""])[0]
        fp = _safe(pathid)
        if not fp or not os.path.isfile(fp):
            return self._send({"error": "no such run: %r" % pathid}, 404)
        try:
            size = os.path.getsize(fp)
        except OSError as e:
            return self._send({"error": str(e)}, 500)
        try:
            offset = int((q.get("offset") or ["0"])[0])
        except ValueError:
            offset = 0
        try:
            mx = min(HARD_MAX, max(1024, int((q.get("max") or [DEFAULT_MAX])[0])))
        except ValueError:
            mx = DEFAULT_MAX
        # offset < 0 => start near the end (initial load of a big file)
        if offset < 0:
            offset = max(0, size - mx)
        # file rotated/shrank -> restart from the top
        if offset > size:
            offset = 0
        data = ""
        try:
            with open(fp, "rb") as fh:
                fh.seek(offset)
                raw = fh.read(mx)
            data = raw.decode("utf-8", "replace")
            offset += len(raw)
        except OSError as e:
            return self._send({"error": str(e)}, 500)
        return self._send({"path": pathid, "data": data, "offset": offset,
                           "size": size, "eof": offset >= size,
                           "ts": time.time()})


def main():
    os.makedirs(RUNS, exist_ok=True)
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    print("LLMOS live server on 0.0.0.0:%d  runs=%s" % (PORT, RUNS))
    srv.serve_forever()


if __name__ == "__main__":
    main()
