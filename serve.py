#!/usr/bin/env python3
"""Local-only static server for Fingertip Bloom."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import socket
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8899
PORT_ATTEMPTS = 20

mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/octet-stream", ".task")


def local_ipv4_addresses() -> list[str]:
    addresses: set[str] = set()

    try:
        hostname = socket.gethostname()
        _, _, host_addresses = socket.gethostbyname_ex(hostname)
        addresses.update(address for address in host_addresses if not address.startswith("127."))
    except OSError:
        pass

    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("192.0.2.1", 80))
        address = probe.getsockname()[0]
        if not address.startswith("127."):
            addresses.add(address)
    except OSError:
        pass
    finally:
        try:
            probe.close()
        except UnboundLocalError:
            pass

    if not addresses:
        try:
            address = socket.gethostbyname(socket.gethostname())
            if not address.startswith("127."):
                addresses.add(address)
        except OSError:
            pass
    return sorted(addresses)


class BloomRequestHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format_string: str, *args) -> None:
        sys.stdout.write("%s - %s\n" % (self.address_string(), format_string % args))
        sys.stdout.flush()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/__lanip":
            body = json.dumps(
                {"ips": local_ipv4_addresses(), "port": self.server.server_port},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        range_header = self.headers.get("Range")
        if range_header and self._serve_range(range_header):
            return
        super().do_GET()

    def _serve_range(self, range_header: str) -> bool:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match:
            return False

        file_path = Path(self.translate_path(self.path))
        if not file_path.is_file():
            return False

        file_size = file_path.stat().st_size
        start = int(match.group(1)) if match.group(1) else 0
        end = int(match.group(2)) if match.group(2) else file_size - 1
        if start > end or start >= file_size:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return True

        end = min(end, file_size - 1)
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(206)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()

        with file_path.open("rb") as stream:
            stream.seek(start)
            remaining = end - start + 1
            while remaining:
                chunk = stream.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)
        return True


class BloomServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def create_server(start_port: int) -> BloomServer:
    for port in range(start_port, start_port + PORT_ATTEMPTS):
        try:
            return BloomServer(("0.0.0.0", port), BloomRequestHandler)
        except OSError:
            continue
    raise OSError(f"No available port in range {start_port}-{start_port + PORT_ATTEMPTS - 1}")


def main() -> None:
    requested_port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            requested_port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            raise SystemExit(2)

    server = create_server(requested_port)
    port = server.server_port
    local_url = f"http://127.0.0.1:{port}/"

    print()
    print("指尖花已启动")
    print(f"电脑打开：{local_url}")
    for address in local_ipv4_addresses():
        print(f"局域网其他设备：http://{address}:{port}/")
    print()
    print("浏览器询问摄像头权限时请选择“允许”。按 Ctrl+C 停止。")
    print()

    threading.Timer(0.35, lambda: webbrowser.open(local_url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
