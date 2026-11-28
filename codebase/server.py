"""Backend HTTP cho bản demo web — chỉ dùng thư viện chuẩn. Hợp đồng API: docs/api.md.

Chạy:  SHP_UI=web python3 run.py              → http://127.0.0.1:8000  (lệnh chính, qua codebase/app.py)
       python3 codebase/server.py            (tương đương)
       SHP_PORT=8080 python3 codebase/server.py
       SHP_CORS_ORIGIN=https://fe.example python3 codebase/server.py   (FE chạy ở địa chỉ khác localhost)

- Chỉ lắng nghe 127.0.0.1 (đổi bằng SHP_HOST nếu thật sự cần).
- Một luồng: tracing của khung giữ một trace tại một thời điểm, và demo chỉ có một người dùng.
- CORS chỉ cho localhost / 127.0.0.1 và SHP_CORS_ORIGIN: trang web lạ mở trên máy demo không gọi được API
  (để không đốt tiền API).
- Không sửa run.py: không đặt SHP_UI thì `python run.py` vẫn là bản dòng lệnh; eval / simulate vẫn gọi agent.answer().
- Trang web (FE): mặc định là giao diện Lextrace ở docs/design/ui/ (có thì dùng), không có thì web/.
  Đổi bằng SHP_WEB_DIR (vd SHP_WEB_DIR=web để dùng bản dự phòng một file). Server trả file tĩnh ở "/", cùng địa chỉ
  với API nên không cần CORS.
"""
import json
import mimetypes
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import service  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _default_web_dir():
    ui = os.path.join(ROOT, "docs", "design", "ui")
    return ui if os.path.isfile(os.path.join(ui, "index.html")) else os.path.join(ROOT, "web")


_env_web = (os.environ.get("SHP_WEB_DIR") or "").strip()
WEB_DIR = (_env_web if os.path.isabs(_env_web) else os.path.join(ROOT, _env_web)) if _env_web else _default_web_dir()
MAX_STATIC = 10 * 1024 * 1024
MAX_BODY = 28 * 1024 * 1024   # zip 20 MB sau base64 (×4/3) ≈ 26,7 MB + phần JSON còn lại
_LOCAL_ORIGIN = re.compile(r"^http://(localhost|127\.0\.0\.1)(:\d{1,5})?$")
_SESSION = re.compile(r"^/api/sessions/([0-9a-f]{32})(/(analyze|business|confirm))?$")


def allowed_origin(origin):
    extra = [o.strip() for o in (os.environ.get("SHP_CORS_ORIGIN") or "").split(",") if o.strip()]
    return bool(origin) and (bool(_LOCAL_ORIGIN.match(origin)) or origin in extra)


class Handler(BaseHTTPRequestHandler):
    server_version = "LexTrace/1.0"

    # -------------------------------------------------------------- tiện ích
    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        origin = self.headers.get("Origin")
        if allowed_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status, code, message, **extra):
        self._send(status, dict({"loi": code, "thong_bao": message}, **extra))

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise service.bad("Content-Length không hợp lệ.")
        if n > MAX_BODY:   # chặn trước khi đọc
            raise service.ServiceError(413, "qua_lon", "Thân request lớn hơn %d MB." % (MAX_BODY // (1024 * 1024)))
        if n == 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise service.bad("Thân request không phải JSON UTF-8 hợp lệ.")

    def _guard_origin(self):
        """Trình duyệt luôn gửi Origin với request khác nguồn: Origin lạ → từ chối, không chạy gì."""
        origin = self.headers.get("Origin")
        if origin and not allowed_origin(origin):
            self._error(403, "nguon_khong_cho_phep", "Origin %s không được phép gọi API." % origin)
            return False
        return True

    def _run(self, fn):
        try:
            status, payload = fn()
            self._send(status, payload)
        except service.ServiceError as e:
            self._error(e.status, e.code, e.message, **e.extra)
        except Exception as e:  # lỗi lạ: không làm chết server, không lộ chi tiết nội bộ
            self.log_error("lỗi xử lý %s: %s: %s", self.path, type(e).__name__, service.ai.mask_key(e))
            self._error(500, "loi_may_chu", "Lỗi máy chủ (%s)." % type(e).__name__)

    # -------------------------------------------------------------- định tuyến
    def do_OPTIONS(self):
        origin = self.headers.get("Origin")
        if not allowed_origin(origin):
            self.send_response(403)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _static(self, path):
        """Trả file tĩnh của FE trong WEB_DIR. Chặn ../, file ẩn, liên kết ra ngoài thư mục."""
        base = os.path.realpath(WEB_DIR)
        rel = path.lstrip("/") or "index.html"
        parts = rel.split("/")
        if any(p in ("", "..") or p.startswith(".") for p in parts):
            return self._error(404, "khong_thay", "Không có trang %s." % path)
        full = os.path.realpath(os.path.join(base, *parts))
        if os.path.isdir(full):
            full = os.path.join(full, "index.html")
        if not full.startswith(base + os.sep) or not os.path.isfile(full) or os.path.getsize(full) > MAX_STATIC:
            if not os.path.isdir(base):
                return self._error(404, "khong_thay", "Chưa có giao diện web (thư mục web/). API ở /api/…, xem docs/api.md.")
            return self._error(404, "khong_thay", "Không có trang %s." % path)
        with open(full, "rb") as f:
            body = f.read()
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._guard_origin():
            return
        path = self.path.split("?", 1)[0]
        if not path.startswith("/api/"):
            return self._static(path)
        routes = {"/api/health": service.health, "/api/options": service.options,
                  "/api/demo-repos": lambda: {"repos": service.list_demo_repos()}}
        if path in routes:
            return self._run(lambda: (200, routes[path]()))
        m = _SESSION.match(path)
        if m and not m.group(2):
            return self._run(lambda: (200, service.status(m.group(1))))
        self._error(404, "khong_thay", "Không có đường dẫn %s." % path)

    def do_POST(self):
        if not self._guard_origin():
            return
        path = self.path.split("?", 1)[0]

        def handle():
            body = self._body()
            if path == "/api/scan":
                return 201, service.scan(body)
            if path == "/api/ask":
                return 200, service.ask(body)
            m = _SESSION.match(path)
            if m and m.group(3) == "analyze":
                return 200, service.analyze(m.group(1))
            if m and m.group(3) == "business":
                return 200, service.business(m.group(1), body)
            if m and m.group(3) == "confirm":
                return 200, service.confirm(m.group(1))
            raise service.ServiceError(404, "khong_thay", "Không có đường dẫn %s." % path)

        self._run(handle)

    def log_message(self, fmt, *args):  # gọn log, không in thân request
        sys.stderr.write("[server] %s - %s\n" % (self.address_string(), fmt % args))


def make_server(host=None, port=None):
    host = host or os.environ.get("SHP_HOST") or "127.0.0.1"
    port = int(port if port is not None else (os.environ.get("SHP_PORT") or 8000))
    return HTTPServer((host, port), Handler)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    httpd = make_server()
    h = service.health()
    print("LexTrace API — http://%s:%d  (chế độ %s, model %s / %s)"
          % (httpd.server_address[0], httpd.server_address[1], h["che_do"], h["model"]["phan_loai"],
             h["model"]["kiem_chung"]))
    print("Hợp đồng API: docs/api.md · Dừng: Ctrl+C")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
