#!/usr/bin/env python3
"""Fake gateway: /v1/models, and /v1/chat/completions answering 503 until a job has run FAKE_LOAD_SECONDS."""
import json, os, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer

STATE = os.environ["FAKE_ROMEO_STATE"]
LOAD = float(os.environ.get("FAKE_LOAD_SECONDS", "2"))


def ready():
    try:
        starts = [float(line.split()[2]) for line in open(os.path.join(STATE, "jobs")) if line.strip()]
    except FileNotFoundError:
        return False
    return any(time.time() - s >= LOAD for s in starts)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        if self.headers.get("Authorization") != "Bearer test-key":
            self.reply(401, {"error": "bad key"})
            return False
        return True

    def do_GET(self):
        if self.authorized():
            self.reply(200, {"data": [{"id": "dsh-deepseek-v4.1-flash-1m"}] if ready() else []})

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.authorized():
            self.reply(200, {"choices": [{"message": {"content": "hi"}}]}) if ready() else self.reply(503, {"error": "loading"})


HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
