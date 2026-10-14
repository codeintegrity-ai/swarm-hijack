#!/usr/bin/env python3
"""Localhost exfil sink for the PoC canary. POST bodies are appended to
exfil.log next to this file. Binds 127.0.0.1 only."""
import http.server
import os
import sys
import time

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exfil.log")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8799


class Sink(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        with open(LOG, "ab") as f:
            f.write(b"=== %s %s %d bytes ===\n" % (time.strftime("%FT%T").encode(), self.path.encode(), n))
            f.write(body + b"\n")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
        print(f"[listener] {self.path} {n} bytes -> {LOG}", flush=True)

    def log_message(self, *a):
        pass


http.server.HTTPServer(("127.0.0.1", PORT), Sink).serve_forever()
