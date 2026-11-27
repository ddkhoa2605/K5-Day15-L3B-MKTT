"""Tầng tĩnh (task M2): đọc schema, tìm lời gọi mạng ra ngoài (sink), tìm dấu hiệu xin đồng ý.

Chỉ phân tích tĩnh mã nguồn: không chạy app, không gọi endpoint, không đọc dữ liệu trong bảng.
Chỉ dùng thư viện chuẩn.

Hai dạng đầu vào cùng đi qua đây:
  - repo trên đĩa: load_repo(path) → {đường_dẫn_tương_đối: nội_dung}
  - Case JSON: files_from_case(case) dựng lại "file ảo" từ các đoạn code trong case,
    columns_from_case(case) đọc các dòng schema dạng "bang(cot1, cot2)".
"""
import json
import os
import re

from legal import normalize

# ---------------------------------------------------------------- lọc secret

_SECRET_PATTERNS = [
    re.compile(r"sk-(?:proj-|ant-)?[A-Za-z0-9_\-]{12,}"),          # OpenAI / Anthropic
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),                         # Google API key
    re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]*\.?[A-Za-z0-9_\-]*"),  # JWT (vd Supabase key)
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9\-]{10,})"),  # GitHub, Slack token
    re.compile(r"(?i)\b([A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*\s*[=:]\s*)(['\"]?)[^\s'\"]{6,}\2"),
]


def redact(text: str) -> str:
    """Thay mọi chuỗi trông như secret bằng [REDACTED] trước khi gửi ra ngoài hay ghi vào case."""
    out = text or ""
    for i, pat in enumerate(_SECRET_PATTERNS):
        if i == len(_SECRET_PATTERNS) - 1:
            out = pat.sub(lambda m: m.group(1) + "[REDACTED]", out)
        else:
            out = pat.sub("[REDACTED]", out)
    return out


# ---------------------------------------------------------------- schema

_CONSTRAINT_WORDS = {"constraint", "primary", "foreign", "unique", "check", "exclude", "like", "index", "key"}
_CREATE_TABLE = re.compile(
    r"create\s+(?:unlogged\s+|temp(?:orary)?\s+)?table\s+(?:if\s+not\s+exists\s+)?"
    r"((?:\"[^\"]+\"|[\w$]+)(?:\s*\.\s*(?:\"[^\"]+\"|[\w$]+))?)\s*\(",
    re.IGNORECASE)


def _table_name(raw: str) -> str:
    """public."Bookings" → bookings (bỏ schema prefix, bỏ ngoặc kép, chuẩn hoá)."""
    parts = re.findall(r"\"[^\"]+\"|[^.\s]+", raw.strip())
    return normalize(parts[-1]) if parts else ""


def _strip_sql_comments(line: str) -> str:
    return re.sub(r"--.*$", "", line)


def parse_schema_line(s: str) -> list:
    """Đọc dòng schema của Case: "users(id, ten, so_dt_kh)" → [{"table", "column"}].
    Bỏ comment "-- …" (có thể chứa câu tấn công). Dòng không có ngoặc → []."""
    s = _strip_sql_comments(s or "").strip()
    m = re.match(r"^\s*((?:\"[^\"]+\"|[^\s(]+))\s*\((.*)\)\s*;?\s*$", s, re.S)
    if not m:
        return []
    table = _table_name(m.group(1))
    cols = []
    for item in _split_top_level(m.group(2)):
        name = _first_token(item)
        if name and normalize(name) not in _CONSTRAINT_WORDS:
            cols.append({"table": table, "column": normalize(name)})
    return cols


def _split_top_level(body: str) -> list:
    """Tách theo dấu phẩy ở mức ngoặc 0 (để numeric(10, 2) không bị tách)."""
    parts, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _first_token(item: str) -> str:
    item = item.strip()
    m = re.match(r"^(\"[^\"]+\"|`[^`]+`|[^\s]+)", item)
    return m.group(1) if m else ""


def parse_sql(sql: str, file=None) -> list:
    """Đọc mọi CREATE TABLE trong một file SQL → [{"table", "column", "file", "line"}].
    Xử lý schema prefix, ngoặc kép, kiểu có dấu phẩy, constraint, comment."""
    text = sql or ""
    clean = "\n".join(_strip_sql_comments(l) for l in text.split("\n"))
    cols = []
    for m in _CREATE_TABLE.finditer(clean):
        table = _table_name(m.group(1))
        start = m.end()  # ngay sau dấu "("
        depth, i = 1, start
        while i < len(clean) and depth:
            if clean[i] == "(":
                depth += 1
            elif clean[i] == ")":
                depth -= 1
            i += 1
        body = clean[start:i - 1]
        offset = start
        for item in _split_top_level(body):
            lead = len(item) - len(item.lstrip())
            name = _first_token(item)
            pos = offset + lead
            offset += len(item) + 1
            if not name or normalize(name) in _CONSTRAINT_WORDS:
                continue
            cols.append({"table": table, "column": normalize(name), "file": file,
                         "line": clean.count("\n", 0, pos) + 1})
    return cols


# ---------------------------------------------------------------- sink

_AI_IMPORT = re.compile(
    r"""(?:from\s+|require\(\s*|import\s+)['"](openai|@anthropic-ai/sdk|@google/generative-ai|@google/genai|"""
    r"""@ai-sdk/(?:openai|anthropic|google)|groq-sdk|@mistralai/mistralai|cohere-ai)['"]""")
_AI_CALL = re.compile(
    r"(chat\.completions\.create|responses\.create|messages\.create|generateContent(?:Stream)?|"
    r"\bgenerateText\s*\(|\bstreamText\s*\(|\bgenerateObject\s*\()")
_AI_URL = re.compile(r"(api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis\.com|"
                     r"api\.groq\.com|api\.mistral\.ai|api\.deepseek\.com)")
_HTTP_CALL = re.compile(r"""\b(?:fetch|axios(?:\.(?:get|post|put|patch|delete|request))?|ky(?:\.\w+)?|got)\s*\(\s*[`'"](https?://[^/'"`\s$]+)""")
_ANALYTICS = re.compile(r"\b(posthog|mixpanel|amplitude|gtag\s*\(|analytics\.(?:track|identify|page)\s*\(|"
                        r"@segment/|hotjar|clarity\s*\(|sentry\.(?:setuser|captureexception|capturemessage|init)\s*\(|"
                        r"logrocket|datadogrum|intercom|hubspot)", re.IGNORECASE)
_EMAIL = re.compile(r"\b(resend\.emails\.send|new\s+Resend\s*\(|sendgrid|@sendgrid/mail|mailgun|nodemailer|"
                    r"mailchimp\.\w+|brevo|sendinblue|postmark)", re.IGNORECASE)
_SDK_IMPORT = re.compile(r"""(?:from\s+|require\(\s*|import\s+)['"](@sentry/[\w\-]+|@mailchimp/[\w\-]+|posthog-js|mixpanel-browser|"""
                         r"""@amplitude/[\w\-]+|resend|@sendgrid/mail|logrocket)['"]""")
_NOT_FOREIGN = (".vn", "localhost", "127.0.0.1", "0.0.0.0")
_SKIP_HTTP_HOSTS = ("supabase.co", "supabase.in")  # kho dữ liệu chính của app, không tính là sink ở lát cắt này

CONTEXT = 5
_STRING_LIT = re.compile(r"""("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)""")
_TRAILING_COMMENT = re.compile(r"(^|\s)//.*$")


_IMPORT_LINE = re.compile(r"""(\brequire\s*\(|^\s*import\b|\bfrom\s+['"])""")


def _code_only(line):
    """Bỏ chuỗi chữ và comment cuối dòng. Dùng cho mẫu nhận diện theo TÊN dịch vụ (analytics, email): tên dịch vụ
    nằm trong chuỗi chữ (vd script sinh tài liệu liệt kê "Mailchimp.com") hay comment không phải lời gọi API.
    Mẫu URL (_AI_URL, _HTTP_CALL) vẫn chạy trên dòng gốc vì URL luôn nằm trong chuỗi.
    Dòng import/require giữ nguyên: chuỗi ở đó là tên gói thật (require("sendgrid"), from "mailgun.js")."""
    if _IMPORT_LINE.search(line):
        return line
    return _TRAILING_COMMENT.sub("", _STRING_LIT.sub('""', line))


def _snippet(lines, idx, ctx=CONTEXT):
    lo, hi = max(0, idx - ctx), min(len(lines), idx + ctx + 1)
    return redact("\n".join(lines[lo:hi])), lo + 1, hi


# ---------------------------------------------------------------- luồng dữ liệu tới lời gọi (C1)
# Ở code thật, dữ liệu cá nhân hay đi qua biến trung gian (dựng danh sách ở một dòng, ghép prompt ở dòng khác, gửi ở
# dòng khác nữa) hoặc qua một hàm bọc định nghĩa ở file khác. Cửa sổ ±CONTEXT dòng quanh lời gọi không thấy được.
# Ba bước, đều là phân tích tĩnh tổng quát, không dựa vào tên biến cụ thể:
#   1. kéo cửa sổ tới hết khối đối số của lời gọi (ngoặc đóng đủ);
#   2. lát cắt ngược: dòng GÁN các biến được dùng trong khối lời gọi, lần ngược tối đa SLICE_HOPS bước trong cùng file;
#   3. hàm bọc: lời gọi nằm trong hàm F có định nghĩa thấy được → mỗi chỗ gọi F( ở file khác cũng là đường ra ngoài.
CALL_MAX = 30      # số dòng tối đa của khối đối số
SLICE_BACK = 200   # lần ngược tối đa bao nhiêu dòng
SLICE_HOPS = 2
SLICE_MAX = 12     # số dòng liên quan tối đa thêm vào một sink
_IDENT = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_NOT_VAR = frozenset("""await async const let var function return new this true false null undefined if else for while
    of in typeof instanceof try catch finally throw import export from default class extends super void delete yield
    JSON Object Array String Number Boolean Math Date Promise console process env fetch window document require
    method headers body POST GET PUT PATCH DELETE then map join filter slice length push""".split())
_FUNC_DEF = re.compile(r"(?:\bfunction\s+([A-Za-z_$][\w$]*)\s*\(|"
                       r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>))")
_NOT_WRAPPER = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "handler", "main", "default", "middleware"})


def _call_end(lines, idx):
    """Dòng cuối của khối đối số bắt đầu ở dòng idx (ngoặc (), {}, [] cân bằng; bỏ qua chuỗi và comment)."""
    depth, opened = 0, False
    for j in range(idx, min(len(lines), idx + CALL_MAX)):
        code = _TRAILING_COMMENT.sub("", _STRING_LIT.sub('""', lines[j]))
        for ch in code:
            if ch in "({[":
                depth, opened = depth + 1, True
            elif ch in ")}]":
                depth -= 1
        if opened and depth <= 0:
            return j
    return idx if not opened else min(len(lines), idx + CALL_MAX) - 1


def _assigns(line, name):
    """Dòng có gán biến name không: const/let/var name =, name =, name +=, hay giải cấu trúc { …name… } = ."""
    code = _STRING_LIT.sub('""', line)
    n = re.escape(name)
    return bool(re.search(r"\b(?:const|let|var)\s+%s\b|(?<![\w$.])%s\s*(?:\+|-)?=(?!=)|"
                          r"\b(?:const|let|var)\s*[{\[][^=]*(?<![\w$])%s(?![\w$])[^=]*[}\]]\s*=(?!=)" % (n, n, n), code))


def _idents(text):
    return {t for t in _IDENT.findall(_STRING_LIT.sub(lambda m: " ".join(re.findall(r"\$\{([^}]*)\}", m.group(0))), text))
            if t not in _NOT_VAR and len(t) >= 2}


def _backward_slice(lines, lo, hi):
    """Dòng (0-index, ngoài cửa sổ [lo, hi]) gán các biến được dùng trong cửa sổ, lần ngược SLICE_HOPS bước."""
    want = set()
    for j in range(lo, hi + 1):
        want |= _idents(lines[j])
    found, start = [], max(0, lo - SLICE_BACK)
    for _ in range(SLICE_HOPS):
        new = set()
        for j in range(lo - 1, start - 1, -1):
            if j in found or not lines[j].strip() or lines[j].lstrip().startswith(("//", "#", "*")):
                continue
            hit = [v for v in want if _assigns(lines[j], v)]
            if hit:
                found.append(j)
                new |= _idents(lines[j]) - set(hit)
                if len(found) >= SLICE_MAX:
                    return sorted(found)
        want = new - want
        if not want:
            break
    return sorted(found)


def _with_related(lines, lo, hi, extra):
    """Đoạn gửi đi: cửa sổ liền mạch + các dòng liên quan (ghi rõ số dòng), đã lọc secret."""
    text = "\n".join(lines[lo:hi + 1])
    if extra:
        text += "\n// … dòng liên quan trong cùng file (gán biến đi vào lời gọi):\n" + "\n".join(
            "// dòng %d: %s" % (j + 1, lines[j].strip()) for j in extra)
    return redact(text)


def _sink_at(path, lines, i, kind, endpoint):
    end = _call_end(lines, i)
    lo, hi = max(0, i - CONTEXT), min(len(lines) - 1, max(i + CONTEXT, end))
    extra = _backward_slice(lines, lo, hi)
    return {"file": path, "line": i + 1, "kind": kind, "endpoint": endpoint,
            "snippet": _with_related(lines, lo, hi, extra), "tu_dong": lo + 1, "den_dong": hi + 1,
            "dong_lien_quan": [j + 1 for j in extra]}


def _enclosing_function(lines, i):
    """Tên hàm bao quanh dòng i (tìm ngược tối đa SLICE_BACK dòng); None nếu không thấy định nghĩa."""
    for j in range(i, max(-1, i - SLICE_BACK), -1):
        m = _FUNC_DEF.search(lines[j])
        if m:
            name = m.group(1) or m.group(2)
            return None if name in _NOT_WRAPPER or len(name) < 4 else name
    return None


def _wrapper_calls(files, sink):
    """Hàm bọc: sink nằm trong hàm F (định nghĩa thấy được) → các chỗ gọi F( ở file khác."""
    lines = files[sink["file"]].split("\n")
    name = _enclosing_function(lines, sink["line"] - 1)
    if not name:
        return []
    call = re.compile(r"(?<![\w$.])%s\s*\(" % re.escape(name))
    out = []
    for path in sorted(files):
        if path == sink["file"]:
            continue
        flines = files[path].split("\n")
        for i, line in enumerate(flines):
            if line.lstrip().startswith(("//", "#", "*")) or _IMPORT_LINE.search(line) or _FUNC_DEF.search(line):
                continue
            if call.search(_STRING_LIT.sub('""', line)):
                s = _sink_at(path, flines, i, sink["kind"], sink["endpoint"])
                s["qua_ham"] = {"ten": name, "file": sink["file"], "line": sink["line"]}
                out.append(s)
                if len(out) >= 5:
                    return out
    return out


def find_sinks(files: dict) -> list:
    """Tìm lời gọi mạng ra ngoài → [{"file", "line", "kind", "endpoint", "snippet", "tu_dong", "den_dong"}].
    kind ∈ ai_nuoc_ngoai · http_ngoai · analytics · email."""
    sinks = []
    for path in sorted(files):
        lines = files[path].split("\n")
        hits = []
        ai_import = None
        for i, line in enumerate(lines):
            if line.lstrip().startswith(("//", "#", "*")):
                continue
            m = _AI_IMPORT.search(line)
            if m:
                ai_import = ai_import or (i, m.group(1))
                continue
            if _SDK_IMPORT.search(line):  # dòng import SDK không phải lời gọi; sink là dòng gọi
                continue
            m = _AI_CALL.search(line) or _AI_URL.search(line)
            if m:
                hits.append((i, "ai_nuoc_ngoai", m.group(1)))
                continue
            m = _HTTP_CALL.search(line)
            if m:
                host = m.group(1).split("://", 1)[1].split(":")[0].lower()
                if not host.endswith(_NOT_FOREIGN) and not host.endswith(_SKIP_HTTP_HOSTS):
                    hits.append((i, "http_ngoai", host))
                continue
            code = _code_only(line)
            m = _ANALYTICS.search(code)
            if m:
                hits.append((i, "analytics", m.group(1).lower()))
                continue
            m = _EMAIL.search(code)
            if m:
                hits.append((i, "email", m.group(1).lower()))
        if ai_import and not any(k == "ai_nuoc_ngoai" for _, k, _ in hits):
            hits.append((ai_import[0], "ai_nuoc_ngoai", ai_import[1]))
        for i, kind, endpoint in sorted(hits):
            sinks.append(_sink_at(path, lines, i, kind, endpoint))
    out, seen = [], set()
    for s in sinks:   # chỗ gọi qua hàm bọc đứng ngay sau sink gốc, để không bị cắt bởi giới hạn số sink gửi model
        out.append(s)
        seen.add((s["file"], s["line"]))
        for w in _wrapper_calls(files, s):
            if (w["file"], w["line"]) not in seen:
                seen.add((w["file"], w["line"]))
                out.append(w)
    return out


# ---------------------------------------------------------------- consent

_CHECKED = re.compile(r"(defaultChecked(?!\s*=\s*\{\s*false\s*\})|checked\s*=\s*\{\s*true\s*\}|checked\s*=\s*['\"]checked['\"]|"
                      r"\bchecked\s*:\s*true|useState\(\s*true\s*\))")
_CONSENT_WORD = re.compile(r"(đồng ý|dong y|chấp nhận|chap nhan|điều khoản|dieu khoan|agree|consent|terms|privacy|"
                           r"nhận tin|nhan tin|bản tin|ban tin|khuyến mãi|khuyen mai|ưu đãi|uu dai|quảng cáo|quang cao|"
                           r"newsletter|marketing|subscribe|promotion|opt.?in)",
                           re.IGNORECASE)
# Ghi bản ghi đồng ý vào một bảng bất kỳ: .from("audit_logs").insert({ … "consent_granted" … })
_CONSENT_INSERT = re.compile(r"""\.from\(\s*['"]([\w.]+)['"]\s*\)\s*\.(?:insert|upsert)\((?=[^\n]*(?:consent|dong_y|đồng ý|dong y))""",
                             re.IGNORECASE)
_SILENCE = re.compile(r"(tiếp tục\s+(?:sử dụng|dùng|truy cập)|tiep tuc\s+(?:su dung|dung|truy cap)|"
                      r"by\s+continuing|continued\s+use)[^\n]{0,120}?(đồng ý|dong y|chấp nhận|chap nhan|agree|accept|consent)",
                      re.IGNORECASE)
_USER_COL = re.compile(r"(^|_)(user|nguoi_dung|khach_hang|khach|customer|profile|account|subject|member|hoc_vien)(_id|id)?($|_)"
                       r"|^uid$|^owner_id$"
                       # Email, SĐT định danh được chủ thể đã đồng ý ("ai"): ND356 Điều 6 yêu cầu kiểm chứng được
                       # chủ thể, thời điểm, nội dung đồng ý, không bắt buộc khoá là user_id.
                       r"|(^|_)(email|e_mail|phone|sdt|so_dt|so_dien_thoai|dien_thoai)($|_)")
_TIME_COL = re.compile(r"(_at$|^thoi_gian|^ngay_|_time$|timestamp|_date$)")
_VERSION_COL = re.compile(r"(version|phien_ban|policy_hash|terms_rev)")
# Cột đồng ý gắn trên bảng khác (vd users.terms_accepted_at). Hai mức:
# - chắc chắn: tên cột tự nói là đồng ý/điều khoản (marketing_consent, terms_version, opt_in…) → nhận bảng.
# - mơ hồ: accepted_at, agreed_at, policy_version cũng gặp ở bảng không liên quan tới đồng ý (hàng đợi email,
#   kết quả thi đấu, mẫu quy trình…) → chỉ nhận khi bảng có khoá người dùng VÀ đủ mốc thời gian + phiên bản
#   trong các cột đồng ý.
_EMBEDDED_STRONG = re.compile(r"(terms|consent|dong_y|dongy|dieu_khoan|privacy|chinh_sach|opt_?in)")
_EMBEDDED_WEAK = re.compile(r"(policy|agree|accept)")
# Tên bảng nhật ký đồng ý: consents, dong_y, user_agreements, terms_acceptances, marketing_opt_ins…
_CONSENT_TABLE = re.compile(r"(consent|dong_?y|agreement|acceptance|opt_?in)")
_USER_TABLE = re.compile(r"^(users?|profiles?|accounts?|customers?|members?|khach(_hang)?|nguoi_dung|hoc_vien|tai_khoan)$")


def find_consent(files: dict, columns: list) -> dict:
    """→ {"bang_consent": str|None, "du_3_truong": bool, "tich_san": [loc], "im_lang_dong_y": [loc]}.
    loc = {"file", "line", "snippet"}. Bảng consent đủ 3 trường = có khoá người dùng + mốc thời gian + phiên bản."""
    by_table = {}
    for c in columns:
        by_table.setdefault(c["table"], []).append(c["column"])
    logged = set()
    for text in files.values():
        for m in _CONSENT_INSERT.finditer(text):
            logged.add(normalize(m.group(1).split(".")[-1]))
    best, full = None, False
    for table, cols in by_table.items():
        if _CONSENT_TABLE.search(table) or table in logged:
            ok = (any(_USER_COL.search(c) for c in cols) and any(_TIME_COL.search(c) for c in cols)
                  and any(_VERSION_COL.search(c) for c in cols))
        else:
            # Đồng ý lưu bằng cột ngay trên bảng người dùng: users(terms_accepted_at, terms_version)
            strong = [c for c in cols if _EMBEDDED_STRONG.search(c)]
            embedded = strong + [c for c in cols if c not in strong and _EMBEDDED_WEAK.search(c)]
            if not embedded:
                continue
            ok = ((_USER_TABLE.search(table) is not None or any(_USER_COL.search(c) for c in cols))
                  and any(_TIME_COL.search(c) for c in embedded) and any(_VERSION_COL.search(c) for c in embedded))
            if not strong and not ok:
                continue  # chỉ có cột mơ hồ mà không đủ 3 trường → không coi là nơi lưu đồng ý
        if best is None or (ok and not full):
            best, full = table, ok
    tich_san, im_lang = [], []
    for path in sorted(files):
        lines = files[path].split("\n")
        for i, line in enumerate(lines):
            if _CHECKED.search(line):
                near = "\n".join(lines[max(0, i - 3): i + 4])
                if _CONSENT_WORD.search(near):
                    tich_san.append({"file": path, "line": i + 1, "snippet": redact(line.strip())})
            if _SILENCE.search(line):
                im_lang.append({"file": path, "line": i + 1, "snippet": redact(line.strip())})
    return {"bang_consent": best, "du_3_truong": full, "tich_san": tich_san, "im_lang_dong_y": im_lang}


# ---------------------------------------------------------------- repo và case

EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".sql", ".json", ".env.example")
SKIP_DIRS = {"node_modules", ".next", ".git", "dist", "build", ".vercel", ".turbo", "coverage"}
MAX_BYTES = 200 * 1024


def load_repo(path: str) -> dict:
    """Đọc file mã nguồn của repo → {đường_dẫn_tương_đối (dấu /): nội_dung}. Bỏ thư mục build, file > 200KB."""
    out = {}
    base = os.path.abspath(path)
    if not os.path.isdir(base):
        raise FileNotFoundError("không thấy thư mục repo: %s" % path)
    for root, dirs, names in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            if not name.endswith(EXTS) or name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock"):
                continue
            full = os.path.join(root, name)
            try:
                if os.path.getsize(full) > MAX_BYTES:
                    continue
                with open(full, encoding="utf-8", errors="replace") as f:
                    out[os.path.relpath(full, base).replace(os.sep, "/")] = f.read()
            except OSError:
                continue
    return out


def repo_columns(files: dict) -> list:
    """Cột lấy từ supabase/migrations/*.sql; repo không có thư mục đó thì lấy mọi file .sql."""
    sql = {p: t for p, t in files.items() if p.endswith(".sql") and "supabase/migrations/" in p}
    if not sql:
        sql = {p: t for p, t in files.items() if p.endswith(".sql")}
    cols = []
    for p in sorted(sql):
        cols += parse_sql(sql[p], p)
    return cols


def _schema_lines(columns: list) -> list:
    tables = {}
    for c in columns:
        tables.setdefault(c["table"], [])
        if c["column"] not in tables[c["table"]]:
            tables[c["table"]].append(c["column"])
    return ["%s(%s)" % (t, ", ".join(cs)) for t, cs in tables.items()]


def _describe(files: dict, path: str) -> str:
    pkg = files.get("package.json")
    if pkg:
        try:
            d = json.loads(pkg)
            if d.get("description"):
                return str(d["description"])[:200]
        except ValueError:
            pass
    return "Repo %s" % os.path.basename(os.path.abspath(path))


def case_from_repo(path: str) -> dict:
    """Dựng Case từ repo. code = các đoạn quanh sink và quanh dấu hiệu consent (đã lọc secret),
    để Case đọc lại bằng files_from_case cho cùng kết luận. Loại hình và quy mô không suy được từ code:
    để "khong_ro" / None cho người dùng xác nhận."""
    files = load_repo(path)
    columns = repo_columns(files)
    wanted = {}
    for s in find_sinks(files):
        wanted.setdefault(s["file"], set()).update(range(s["tu_dong"], s["den_dong"] + 1))
        wanted[s["file"]].update(s.get("dong_lien_quan") or [])
    consent = find_consent(files, columns)
    for loc in consent["tich_san"]:
        wanted.setdefault(loc["file"], set()).update(range(max(1, loc["line"] - 3), loc["line"] + 4))
    for loc in consent["im_lang_dong_y"]:
        wanted.setdefault(loc["file"], set()).add(loc["line"])
    for p, text in files.items():  # dòng ghi bản ghi đồng ý: giữ để Case đọc lại vẫn nhận ra bảng consent
        for m in _CONSENT_INSERT.finditer(text):
            wanted.setdefault(p, set()).add(text.count("\n", 0, m.start()) + 1)
    code = []
    for p in sorted(wanted):
        lines = files[p].split("\n")
        run = []
        for n in sorted(l for l in wanted[p] if 1 <= l <= len(lines)):
            if run and n != run[-1] + 1:
                code.append({"file": p, "line": run[0], "text": redact("\n".join(lines[run[0] - 1: run[-1]]))})
                run = []
            run.append(n)
        if run:
            code.append({"file": p, "line": run[0], "text": redact("\n".join(lines[run[0] - 1: run[-1]]))})
    return {"id": "repo:" + os.path.basename(os.path.abspath(path)), "mo_ta": _describe(files, path),
            "schema": _schema_lines(columns), "code": code,
            "loai_hinh": "khong_ro", "so_chu_the_luy_ke": None}


def files_from_case(case: dict) -> dict:
    """Dựng lại "file ảo" từ case["code"]: mỗi đoạn đặt đúng dòng bắt đầu của nó, dòng khác để trống."""
    files = {}
    for c in case.get("code") or []:
        if not isinstance(c, dict):
            continue
        path = str(c.get("file") or "input")
        try:
            start = max(1, int(c.get("line") or 1))
        except (TypeError, ValueError):
            start = 1
        buf = files.setdefault(path, [])
        for k, text in enumerate(str(c.get("text") or "").split("\n")):
            idx = start - 1 + k
            while len(buf) <= idx:
                buf.append("")
            buf[idx] = text
    return {p: "\n".join(lines) for p, lines in files.items()}


def columns_from_case(case: dict) -> list:
    cols = []
    for line in case.get("schema") or []:
        cols += parse_schema_line(str(line))
    return cols
