"""Deterministic HTTP fixture; never connects to or evaluates a real model."""
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def translated(payload):
    request = json.loads(payload["messages"][-1]["content"])
    return {"translations": [
        {"id": line["id"], "text": "한국어 번역 " + str(line["id"])}
        for line in request["input"]
    ]}


@contextmanager
def mock_ollama(actions=(), *, raw=False):
    calls = []
    pending = list(actions)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((self.path, payload))
            action = pending.pop(0) if pending else translated
            if callable(action):
                status, content = 200, action(payload)
            else:
                status, content = action
            if status == 200 and not raw:
                text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
                if self.path.endswith("/chat/completions"):
                    content = {"choices": [{"finish_reason": "stop", "message": {"content": text}}]}
                else:
                    content = {"done": True, "done_reason": "stop", "message": {"content": text}}
            body = json.dumps(content, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
