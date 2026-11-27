"""Lớp dịch vụ cho bản demo web (docs/api.md). Không phụ thuộc HTTP — server.py chỉ chuyển request vào đây.

Luồng hai bước (spec.md §4, §9): scan() chỉ quét tĩnh và trả ĐÚNG những gì sẽ gửi ra model; người dùng bấm gửi
thì analyze() mới gọi model. business() sửa loại hình / số chủ thể và chỉ chạy lại rule engine (spec.md §6),
confirm() sinh bản nháp hồ sơ từ kết luận mới nhất. answer() ở agent.py không đổi; các bước ở đây gọi cùng các
công cụ trong tools.py theo cùng thứ tự với agent._pipeline.
"""
import base64
import binascii
import io
import os
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
import zipfile

import ai
import legal
import report
import scanner
import tracing
import tools
from tools import MAX_STEPS, apply_rules, classify_columns, draft_dpia, verify_paths

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.environ.get("SHP_DEMO_DIR") or os.path.join(ROOT, "data", "demo_repos")

MAX_ZIP_BYTES = 20 * 1024 * 1024        # file .zip tải lên / tải từ GitHub
MAX_ZIP_MEMBERS = 5000                  # số mục tối đa trong zip
MAX_ZIP_TOTAL = 60 * 1024 * 1024        # tổng số byte được đọc ra từ zip
SESSION_TTL = 60 * 60                   # giây
MAX_SESSIONS = 100
GITHUB_TIMEOUT = 30

LOAI_HINH = {"ho_kinh_doanh": "Hộ kinh doanh", "doanh_nghiep_sieu_nho": "Doanh nghiệp siêu nhỏ",
             "doanh_nghiep_nho": "Doanh nghiệp nhỏ", "khoi_nghiep": "Doanh nghiệp khởi nghiệp sáng tạo",
             "doanh_nghiep_lon": "Doanh nghiệp vừa, lớn", "khong_ro": "Chưa rõ"}
WEB_MODES = ("hybrid", "rule")          # llm = ablation B, không đưa cho người dùng
_GITHUB = re.compile(r"^https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100}?)(?:\.git)?/?$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class ServiceError(Exception):
    """Lỗi có mã cho API: status HTTP + mã `loi` + thông điệp cho người đọc."""

    def __init__(self, status, code, message, **extra):
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


def bad(message):
    return ServiceError(400, "dau_vao_sai", message)


# ---------------------------------------------------------------- phiên

_sessions = {}
_lock = threading.Lock()


def _new_session(data):
    now = time.time()
    with _lock:
        for sid in [s for s, v in _sessions.items() if now - v["t"] > SESSION_TTL]:
            del _sessions[sid]
        while len(_sessions) >= MAX_SESSIONS:
            del _sessions[min(_sessions, key=lambda s: _sessions[s]["t"])]
        sid = uuid.uuid4().hex
        data["t"] = now
        _sessions[sid] = data
    return sid


def _get(sid):
    with _lock:
        s = _sessions.get(sid)
        if s is None or time.time() - s["t"] > SESSION_TTL:
            _sessions.pop(sid, None)
            raise ServiceError(404, "khong_thay", "Không có phiên này hoặc phiên đã hết hạn — hãy quét lại.")
        s["t"] = time.time()
        return s


# ---------------------------------------------------------------- nguồn: zip, GitHub, repo demo

def files_from_zip(data: bytes) -> dict:
    """Đọc mã nguồn trong file .zip NGAY TRONG BỘ NHỚ (không giải nén ra đĩa), cùng bộ lọc với scanner.load_repo.
    Không tin kích thước khai trong zip: mỗi file đọc tối đa MAX_BYTES+1 byte, có trần số mục và tổng byte."""
    if len(data) > MAX_ZIP_BYTES:
        raise ServiceError(413, "qua_lon", "File zip lớn hơn %d MB." % (MAX_ZIP_BYTES // (1024 * 1024)))
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise bad("File tải lên không phải file .zip hợp lệ.")
    infos = zf.infolist()
    if len(infos) > MAX_ZIP_MEMBERS:
        raise ServiceError(413, "qua_lon", "File zip có quá nhiều mục (> %d)." % MAX_ZIP_MEMBERS)
    names = []
    for info in infos:
        name = info.filename.replace("\\", "/")
        parts = [p for p in name.split("/") if p not in ("", ".")]
        if info.is_dir() or name.startswith("/") or ".." in parts or not parts:
            continue
        if (info.external_attr >> 16) & 0o170000 == 0o120000:   # liên kết tượng trưng
            continue
        names.append((info, parts))
    # Zip của GitHub (và nhiều zip nén cả thư mục) có đúng một thư mục gốc: bỏ nó đi.
    tops = {parts[0] for _, parts in names}
    strip = 1 if len(tops) == 1 and all(len(parts) > 1 for _, parts in names) else 0
    out, total = {}, 0
    for info, parts in names:
        parts = parts[strip:]
        if any(p in scanner.SKIP_DIRS for p in parts[:-1]):
            continue
        fname = parts[-1]
        if not fname.endswith(scanner.EXTS) or fname in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock"):
            continue
        with zf.open(info) as f:
            raw = f.read(scanner.MAX_BYTES + 1)
        total += len(raw)
        if total > MAX_ZIP_TOTAL:
            raise ServiceError(413, "qua_lon", "Nội dung giải nén vượt %d MB." % (MAX_ZIP_TOTAL // (1024 * 1024)))
        if len(raw) > scanner.MAX_BYTES:
            continue
        out["/".join(parts)] = raw.decode("utf-8", errors="replace")
    return out


class _NoRedirectOutsideCodeload(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith("https://codeload.github.com/"):
            raise ServiceError(404, "khong_thay", "GitHub chuyển hướng tới địa chỉ lạ, không tải.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_github_zip(url: str):
    """Tải bản zip nhánh mặc định của một repo GitHub CÔNG KHAI. Chỉ nhận https://github.com/<owner>/<repo>,
    chỉ gọi codeload.github.com, có timeout và trần dung lượng. → (bytes, "owner/repo")."""
    m = _GITHUB.match((url or "").strip())
    if not m:
        raise bad("Link GitHub phải có dạng https://github.com/<owner>/<repo>.")
    owner, repo = m.group(1), m.group(2)
    zurl = "https://codeload.github.com/%s/%s/zip/HEAD" % (owner, repo)
    opener = urllib.request.build_opener(_NoRedirectOutsideCodeload)
    req = urllib.request.Request(zurl, headers={"User-Agent": "ship-hop-phap-demo"})
    try:
        with opener.open(req, timeout=GITHUB_TIMEOUT) as r:
            data = r.read(MAX_ZIP_BYTES + 1)
    except urllib.error.HTTPError as e:
        e.close()
        raise ServiceError(404, "khong_thay", "Không tải được repo (HTTP %d). Repo phải công khai." % e.code)
    except (urllib.error.URLError, OSError) as e:
        raise ServiceError(404, "khong_thay", "Không kết nối được GitHub (%s)." % getattr(e, "reason", e))
    if len(data) > MAX_ZIP_BYTES:
        raise ServiceError(413, "qua_lon", "Repo lớn hơn %d MB." % (MAX_ZIP_BYTES // (1024 * 1024)))
    return data, "%s/%s" % (owner, repo)


def list_demo_repos(demo_dir=None) -> list:
    base = demo_dir or DEMO_DIR
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        if os.path.isdir(path) and _SAFE_ID.match(name):
            out.append({"id": name, "mo_ta": scanner.case_from_repo(path)["mo_ta"]})
    return out


# ---------------------------------------------------------------- xem trước "sẽ gửi gì ra ngoài"

def _mode(requested=None):
    env = (os.environ.get("SHP_MODE") or "").strip().lower()
    m = (requested or (env if env in WEB_MODES else "hybrid")).strip().lower()
    if m not in WEB_MODES:
        raise bad("Chế độ %r không dùng trên web (chỉ: %s)." % (m, ", ".join(WEB_MODES)))
    return m


def preview(ctx: dict, mode: str) -> dict:
    """ĐÚNG những gì analyze() sẽ gửi cho model — cùng nguồn với prompt ở classify_llm và verify_path_llm."""
    if mode == "rule":
        return {"model_phan_loai": None, "model_kiem_chung": None,
                "khong_gui": "Chế độ rule: không gọi model, không gửi gì ra ngoài."}
    mo_ta = scanner.redact((ctx["case"].get("mo_ta") or "")[:400])
    cols = ["%s.%s (tên cột)" % (c["table"], c["column"]) for c in ctx["columns"]]
    snippets = [{"file": s["file"], "tu_dong": s["tu_dong"], "den_dong": s["den_dong"],
                 "text": scanner.redact(s.get("snippet", ""))} for s in ctx["sinks"][:MAX_STEPS]]
    return {
        "model_phan_loai": {"model": ai.MODEL_NAME or None,
                            "noi_dung": (["mô tả app (đã lọc secret): " + mo_ta] if mo_ta else []) + cols}
        if ctx["columns"] else None,
        "model_kiem_chung": {"model": ai.verify_model() or None,
                             "noi_dung": ["%s:%s-%s (đoạn code đã lọc secret)" % (s["file"], s["tu_dong"], s["den_dong"])
                                          for s in snippets],
                             "doan_code": snippets,
                             "kem_ten_cot_ca_nhan": "tên các cột được xếp là dữ liệu cá nhân ở bước phân loại"}
        if snippets else None,
        "khong_gui": "Không gửi dữ liệu trong bảng, không gửi file khác, không gửi API key (đã thay bằng [REDACTED]).",
    }


def _missing(case):
    miss = []
    if case.get("loai_hinh") in (None, "khong_ro"):
        miss.append("loai_hinh")
    if case.get("so_chu_the_luy_ke") is None:
        miss.append("so_chu_the_luy_ke")
    return miss


def _business_fields(body, require_one=False):
    out = {}
    if "loai_hinh" in body and body["loai_hinh"] is not None:
        if body["loai_hinh"] not in LOAI_HINH:
            raise bad("loai_hinh phải là một trong: %s." % ", ".join(LOAI_HINH))
        out["loai_hinh"] = body["loai_hinh"]
    if "so_chu_the_luy_ke" in body and body["so_chu_the_luy_ke"] is not None:
        v = body["so_chu_the_luy_ke"]
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise bad("so_chu_the_luy_ke phải là số nguyên ≥ 0.")
        out["so_chu_the_luy_ke"] = v
    if require_one and not out:
        raise bad("Cần ít nhất một trong loai_hinh, so_chu_the_luy_ke.")
    return out


# ---------------------------------------------------------------- các bước

def scan(body: dict) -> dict:
    """POST /api/scan — quét tĩnh, không gọi model."""
    if not isinstance(body, dict):
        raise bad("Thân request phải là JSON object.")
    sources = [k for k in ("demo_repo", "case", "zip_base64", "github_url") if body.get(k) not in (None, "")]
    if len(sources) != 1:
        raise bad("Gửi đúng một nguồn: demo_repo, case, zip_base64 hoặc github_url.")
    src = sources[0]
    mode = _mode(body.get("che_do"))
    biz = _business_fields(body)
    if src == "case":
        case = body["case"]
        if not isinstance(case, dict) or not (case.get("schema") or case.get("code")):
            raise bad('case phải là JSON object có "schema" hoặc "code".')
        case = dict(case)
        if isinstance(case.get("schema"), str):
            case["schema"] = [case["schema"]]
        files, columns, nguon = scanner.files_from_case(case), scanner.columns_from_case(case), {"loai": "case"}
    else:
        if src == "demo_repo":
            rid = str(body["demo_repo"])
            path = os.path.join(DEMO_DIR, rid)
            if not _SAFE_ID.match(rid) or not os.path.isdir(path):
                raise ServiceError(404, "khong_thay", "Không có repo demo %r." % rid)
            files, name = scanner.load_repo(path), rid
        elif src == "zip_base64":
            try:
                raw = base64.b64decode(body["zip_base64"], validate=True)
            except (binascii.Error, ValueError, TypeError):
                raise bad("zip_base64 không phải base64 hợp lệ.")
            name = os.path.splitext(os.path.basename(str(body.get("ten_file") or "upload.zip")))[0] or "upload"
            files = files_from_zip(raw)
        else:
            raw, name = fetch_github_zip(body["github_url"])
            files = files_from_zip(raw)
        if not files:
            raise bad("Không thấy file mã nguồn nào đọc được (.ts, .tsx, .js, .sql…).")
        case = scanner.case_from_files(files, name)
        columns = scanner.repo_columns(files)
        nguon = {"loai": src, "ten": name}
    case.update(biz)
    ctx = tools._context(case, files, columns)   # cùng hàm scan_repo / scan_case dùng
    sid = _new_session({"ctx": ctx, "mode": mode, "nguon": nguon, "buoc": "da_quet"})
    warn = []
    if mode != "rule" and len(ctx["sinks"]) > MAX_STEPS:
        warn.append("Repo có %d lời gọi ra ngoài, chỉ %d lời gọi đầu được gửi model kiểm chứng."
                    % (len(ctx["sinks"]), MAX_STEPS))
    c = ctx["consent"]
    return {
        "session_id": sid, "nguon": nguon, "che_do": mode, "mo_ta": case.get("mo_ta") or "",
        "thong_ke": {"so_file": len(ctx["files"]), "so_cot": len(ctx["columns"]), "so_loi_goi_ra_ngoai": len(ctx["sinks"])},
        "cot": [{"table": x["table"], "column": x["column"], "file": x.get("file"), "line": x.get("line")}
                for x in ctx["columns"]],
        "loi_goi_ra_ngoai": [{"file": s["file"], "line": s["line"], "loai": s["kind"], "dich": s["endpoint"],
                              "dong": s.get("dong", "")} for s in ctx["sinks"]],
        "dong_y": {"bang": c["bang_consent"], "du_3_truong": c["du_3_truong"],
                   "tich_san": c["tich_san"], "im_lang_dong_y": c["im_lang_dong_y"]},
        "se_gui_ra_ngoai": preview(ctx, mode),
        "thieu_thong_tin": _missing(case),
        "canh_bao": warn,
    }


def _sent(mode, ctx, paths):
    if mode == "rule":
        return []
    sent = []
    mo_ta = scanner.redact((ctx["case"].get("mo_ta") or "")[:400])
    if ctx["columns"] and mo_ta:
        sent.append("mô tả app (đã lọc secret)")
    sent += ["%s.%s (tên cột)" % (c["table"], c["column"]) for c in ctx["columns"]]
    sent += ["%s:%s-%s (đã lọc secret)" % (p["sink"]["file"], p["sink"]["tu_dong"], p["sink"]["den_dong"])
             for p in paths if "tu_dong" in p["sink"]]
    return sent


def _result(sid, s, usage):
    ctx, findings = s["ctx"], s["findings"]
    ket_qua = {}
    for k in ("C1", "C2", "C3"):
        f = dict(findings[k])
        f["ten"] = report.TEN[k]
        f["can_cu"] = [{"ma": code, "noi_dung": legal.cite(code)} for code in f["can_cu"]]
        ket_qua[k] = f
    warn = []
    if s["mode"] != "rule" and len(ctx["sinks"]) > MAX_STEPS:
        warn.append("Repo có %d lời gọi ra ngoài, mới kiểm %d lời gọi đầu." % (len(ctx["sinks"]), MAX_STEPS))
    text = report.render(findings, s["sent"], message=" ".join(warn), mo_ta=ctx["case"].get("mo_ta") or "",
                         mode=s["mode"])
    return {"session_id": sid, "che_do": s["mode"], "ket_qua": ket_qua, "da_gui_ra_ngoai": s["sent"],
            "thieu_thong_tin": _missing(ctx["case"]), "canh_bao": warn, "luu_y": report.DISCLAIMER,
            "bao_cao_text": text.rsplit("\n```json", 1)[0].rstrip(), "su_dung": usage}


def _traced(name, fn):
    """Bọc một bước bằng tracing.begin/end để đếm lời gọi model và token (khung chỉ có một trace tại một thời điểm)."""
    tracing.begin(name)
    try:
        res = fn()
    finally:
        summary, _ = tracing.end()
    return res, {"so_lan_goi_model": summary["model_calls"], "token_vao": summary["tokens_in"],
                 "token_ra": summary["tokens_out"]}


def analyze(sid: str) -> dict:
    """POST /api/sessions/{id}/analyze — gọi model (hybrid) + rule engine. Gọi lại trả kết quả đã có."""
    s = _get(sid)
    if s.get("findings") is not None:
        return _result(sid, s, {"so_lan_goi_model": 0, "token_vao": 0, "token_ra": 0})
    ctx, mode = s["ctx"], s["mode"]

    def run():  # cùng thứ tự với agent._pipeline
        labels = classify_columns(ctx["columns"], ctx["case"].get("mo_ta") or "", mode)
        personal = legal.sensitive_groups() | {"pii_co_ban"}
        pii = [l for l in labels if l["nhom"] in personal and l["do_tin_cay"] >= 0.5]
        paths = verify_paths(ctx["sinks"], pii, mode)
        return labels, paths, apply_rules(ctx["case"], labels, paths, ctx["consent"])

    try:
        (labels, paths, findings), usage = _traced("web:analyze", run)
    except RuntimeError as e:   # ai.py đã thử lại và che API key
        raise ServiceError(502, "loi_model", "Gọi model lỗi: %s" % ai.mask_key(e))
    s.update(labels=labels, paths=paths, findings=findings, sent=_sent(mode, ctx, paths), buoc="da_phan_tich")
    return _result(sid, s, usage)


def business(sid: str, body: dict) -> dict:
    """POST /api/sessions/{id}/business — sửa loại hình / số chủ thể, CHỈ chạy lại rule engine (không gọi model)."""
    s = _get(sid)
    biz = _business_fields(body if isinstance(body, dict) else {}, require_one=True)
    s["ctx"]["case"].update(biz)
    if s.get("findings") is None:
        raise ServiceError(409, "sai_thu_tu", "Đã lưu thông tin doanh nghiệp, nhưng phải phân tích (analyze) trước.")
    ctx = s["ctx"]
    findings, usage = _traced("web:business",
                              lambda: apply_rules(ctx["case"], s["labels"], s["paths"], ctx["consent"]))
    s.update(findings=findings, buoc="da_phan_tich")
    return _result(sid, s, usage)


def confirm(sid: str) -> dict:
    """POST /api/sessions/{id}/confirm — người chịu trách nhiệm xác nhận → bản nháp (không gửi, không nộp)."""
    s = _get(sid)
    if s.get("findings") is None:
        raise ServiceError(409, "sai_thu_tu", "Chưa có kết luận để xác nhận — hãy phân tích (analyze) trước.")
    draft, _ = _traced("web:confirm", lambda: draft_dpia(s["findings"]))
    s["buoc"] = "da_xac_nhan"
    return {"ban_nhap_markdown": draft,
            "ket_qua_da_xac_nhan": {k: s["findings"][k]["trang_thai"] for k in ("C1", "C2", "C3")}}


def status(sid: str) -> dict:
    s = _get(sid)
    case = s["ctx"]["case"]
    return {"session_id": sid, "buoc": s["buoc"], "nguon": s["nguon"], "che_do": s["mode"],
            "loai_hinh": case.get("loai_hinh"), "so_chu_the_luy_ke": case.get("so_chu_the_luy_ke")}


def ask(body: dict) -> dict:
    """POST /api/ask — như ô nhập của bản dòng lệnh, dùng cho nhánh tự từ chối."""
    import agent
    text = body.get("text") if isinstance(body, dict) else None
    if not isinstance(text, str) or not text.strip():
        raise bad("Cần trường text.")
    kind, val = agent._parse_input(text)
    if kind == "refuse":
        raise ServiceError(400, "tu_choi", val, huong_dan=report.FORMAT_HELP)
    raise bad("Đầu vào hợp lệ — hãy dùng /api/scan (repo demo, JSON, zip hoặc link GitHub).")


def health() -> dict:
    provider = ai.MODEL_PROVIDER
    return {"ok": True, "che_do": _mode(),
            "model": {"provider": provider, "phan_loai": ai.MODEL_NAME or None,
                      "kiem_chung": ai.verify_model() or None}}


def options() -> dict:
    return {"loai_hinh": [{"ma": k, "ten": v} for k, v in LOAI_HINH.items()]}
