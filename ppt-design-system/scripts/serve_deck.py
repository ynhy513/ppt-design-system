"""Open one reviewed deck in a local editor with direct PPTX and PDF downloads."""

import argparse
from binascii import Error as Base64Error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from secrets import token_urlsafe
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import quote
from zipfile import BadZipFile

from jsonschema import ValidationError
from PIL import Image

from make_deck import make, require


MAX_REQUEST = 64 * 1024**2
FORMATS = {
    "/export/pptx": ("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    "/export/pdf": ("pdf", "application/pdf"),
}
EXPORT_ERRORS = (ValueError, TypeError, KeyError, OSError, BadZipFile, Base64Error,
                 Image.DecompressionBombError, ValidationError)


def serve(args):
    token = token_urlsafe(24)
    name = re.sub(r"[^\w .-]", "_", args.name or args.manuscript.stem).strip(". ")[:100] or "deck"
    with TemporaryDirectory() as temporary:
        stage = Path(temporary) / "preview"
        stage.mkdir()
        preview_args = argparse.Namespace(**{**vars(args), "html_only": True})
        require(make(preview_args, stage, export_token=token), "文稿含未匹配页面，请先审阅制作报告。")
        editor = (stage / "deck.html").read_bytes()

    class EditorRequest(BaseHTTPRequestHandler):
        def respond(self, status, data, mime, filename=None):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if filename:
                self.send_header("Content-Disposition", "attachment; filename=\"deck." + filename
                                 + "\"; filename*=UTF-8''" + quote(f"{name}.{filename}", safe=""))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def error(self, status, message):
            self.respond(status, json.dumps({"error": message}, ensure_ascii=False).encode(),
                         "application/json; charset=utf-8")

        @property
        def address(self):
            return f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if self.path != "/" or self.headers.get("Host") != self.address:
                self.error(404, "找不到该页面。")
                return
            self.respond(200, editor, "text/html; charset=utf-8")

        def do_POST(self):
            if (self.headers.get("Host") != self.address
                    or self.headers.get("Origin") != f"http://{self.address}"
                    or self.headers.get("X-Deck-Session") != token):
                self.error(403, "请从当前编辑页发起导出。")
                return
            if self.path not in FORMATS:
                self.error(404, "不支持此导出格式。")
                return
            extension, mime = FORMATS[self.path]
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = 0
            if self.headers.get_content_type() != "application/json" or not 0 < size <= MAX_REQUEST:
                self.error(400, "修改文件为空、格式不正确或超过 64 MB。")
                return
            try:
                self.connection.settimeout(30)
                data = self.rfile.read(size)
                require(len(data) == size, "修改传输不完整，请重试。")
                with TemporaryDirectory() as temporary:
                    folder = Path(temporary)
                    edits = folder / "edits.json"
                    edits.write_bytes(data)
                    stage = folder / "export"
                    stage.mkdir()
                    request_args = argparse.Namespace(**{**vars(args), "edits": edits, "html_only": extension == "pdf"})
                    require(make(request_args, stage), "文稿含未匹配页面，请先审阅制作报告。")
                    result = stage / f"deck.{extension}"
                    if extension == "pdf":
                        subprocess.run([args.node, str(Path(__file__).with_name("export_pdf.cjs")),
                                        str(stage / "replay.html"), str(result)],
                                       check=True, capture_output=True, text=True, timeout=90)
                    exported = result.read_bytes()
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as error:
                print(getattr(error, "stderr", None) or str(error), file=sys.stderr)
                self.error(500, "导出暂时失败，修改仍在编辑页。PDF 需要本机 Chromium 和 Playwright。")
                return
            except EXPORT_ERRORS as error:
                message = str(error)
                if "Native PPTX does not support curve" in message:
                    message = "此稿含原生 PPTX 暂不支持的曲线，可以导出 PDF。"
                self.error(422, message)
                return
            self.respond(200, exported, mime, extension)

    with ThreadingHTTPServer(("127.0.0.1", args.port), EditorRequest) as server:
        print(f"打开编辑稿  http://127.0.0.1:{server.server_port}/", flush=True)
        server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path, help="Reviewed design pack directory or ZIP")
    parser.add_argument("manuscript", type=Path, help="Confirmed semantic manuscript")
    parser.add_argument("--assets", type=Path, help="Replaceable content assets")
    parser.add_argument("--source", type=Path, help="Verify source and artwork")
    parser.add_argument("--edits", type=Path, help="Initial edits saved from the editor")
    parser.add_argument("--port", type=int, default=8769, help="Local editor port")
    parser.add_argument("--name", help="Download filename without extension")
    parser.add_argument("--node", default="node", help="Node.js executable for PDF export")
    args = parser.parse_args()
    try:
        serve(args)
    except KeyboardInterrupt:
        return
    except EXPORT_ERRORS as error:
        parser.exit(2, f"无法启动编辑页：{error}\n")


if __name__ == "__main__":
    main()
