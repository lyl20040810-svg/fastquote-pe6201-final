"""Run the FastQuote local web application."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from fastquote.config import load_dotenv
from fastquote.service import QuoteService


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
SERVICE = QuoteService(ROOT)


class Handler(BaseHTTPRequestHandler):
    server_version = "FastQuote/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json({"status": "ok", "catalog_rows": len(SERVICE.catalog.rows)})
            return
        relative = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
        target = (STATIC / relative).resolve()
        if STATIC.resolve() not in target.parents and target != STATIC.resolve():
            self.send_error(403)
            return
        if not target.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        content = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/quote":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = SERVICE.quote(str(payload.get("request", "")), str(payload.get("mode", "auto")))
            self._json(result)
        except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
            self._json({"processing_status": "error", "message": str(exc)}, status=400)
        except Exception:
            self._json(
                {"processing_status": "error", "message": "Unexpected server error."},
                status=500,
            )

    def log_message(self, format: str, *args: object) -> None:
        print(f"[FastQuote] {self.address_string()} {format % args}")

    def _json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Run FastQuote locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.getenv("FASTQUOTE_PORT", "8765")))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"FastQuote is running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

