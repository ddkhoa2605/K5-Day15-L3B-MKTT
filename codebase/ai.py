"""Nối model — chỗ DUY NHẤT trong bản chạy thử gọi model AI. NHÓM VIẾT phần gọi model thật.

Hợp đồng (giữ nguyên để khung đo được token):
    call_model(system: str, user: str) -> dict với 4 khoá
        "text":       str   chữ model trả về
        "model":      str   tên model đã gọi (để tra giá ở bảng giá model)
        "tokens_in":  int   số token vào, lấy từ trường usage trong phản hồi API — KHÔNG ước lượng
        "tokens_out": int   số token ra, gồm cả token suy luận / suy nghĩ nếu API tính riêng
    @model_call (từ tracing.py) tự ghi mỗi lần gọi vào trace; agent.py gọi call_model bao nhiêu lần
    cũng được, khung tự cộng token.
    Lỗi gọi model (hết lượt, sai key, mất mạng): cứ để exception bay ra — khung ghi lỗi vào cột error.

Chế độ giả (mặc định khi .env chưa có MODEL_PROVIDER, hoặc MODEL_PROVIDER=fake):
    trả một câu giả cố định, model "fake", token 0 — để luồng chạy hết từ trước CP2 (guide bước 3.2).
    Lượt `run.py eval` / `run.py simulate` chạy bằng model giả KHÔNG được tính.

Nối model thật: điền .env (chép từ .env.example), rồi viết nhánh gọi API ở dưới theo docs/connect-model.md
(có ví dụ OpenAI, Claude, model chạy trên máy, và cách nối nhà cung cấp khác). Không dán API key vào file này.
"""
import json
import os
import socket
import time
import urllib.error
import urllib.request

from tracing import model_call

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path=os.path.join(ROOT, ".env")):
    """Đọc file .env (KEY=VALUE mỗi dòng) vào biến môi trường, không ghi đè biến đã có. Khung — không cần sửa."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
MODEL_PROVIDER = (os.environ.get("MODEL_PROVIDER") or "fake").strip().lower()
MODEL_NAME = (os.environ.get("MODEL_NAME") or "").strip()
API_KEY = (os.environ.get("API_KEY") or "").strip()
# Model thứ hai (spec §4): MODEL_NAME = model nhỏ phân loại cột · MODEL_NAME_VERIFY = model mạnh kiểm đường đi.
# Để trống MODEL_NAME_VERIFY thì kiểm đường đi cũng dùng MODEL_NAME.
MODEL_NAME_VERIFY = (os.environ.get("MODEL_NAME_VERIFY") or "").strip()


def _env_num(name, kind):
    """Biến .env dạng số, tuỳ chọn: trống → None (dùng mặc định của model). Sai dạng → báo lỗi rõ."""
    v = (os.environ.get(name) or "").strip()
    if not v:
        return None
    try:
        return kind(v)
    except ValueError:
        raise RuntimeError("%s=%r trong .env không phải số" % (name, v))


# Tuỳ chọn, để các lượt so được với nhau và giữ ngân sách. Trống = mặc định của model.
# Model suy luận (vd gpt-6-luna) tính cả token suy nghĩ vào trần: đặt trần đủ lớn, nếu không `content` sẽ rỗng.
# Một số model suy luận không nhận temperature: khi đó để trống.
MODEL_MAX_TOKENS = _env_num("MODEL_MAX_TOKENS", int)
MODEL_TEMPERATURE = _env_num("MODEL_TEMPERATURE", float)
CLAUDE_DEFAULT_MAX_TOKENS = 1024   # API Claude bắt buộc max_tokens
RETRY_WAITS = (2, 4)               # giây chờ trước lần thử lại thứ 1, 2 (tổng 3 lần gọi)
RETRY_STATUS = {408, 409, 429}     # cộng mọi mã 5xx
SHOW_RAW = False   # đổi thành True để in nguyên phản hồi của API khi cần tìm tên trường
URL_OPENAI = "https://api.openai.com/v1/chat/completions"
URL_CLAUDE = "https://api.anthropic.com/v1/messages"


def verify_model() -> str:
    """Tên model dùng cho bước kiểm chứng đường đi (verify_path_llm)."""
    return MODEL_NAME_VERIFY or MODEL_NAME


def mask_key(text):
    """Che API key trong mọi thông điệp lỗi: lỗi được ghi vào cột error của eval/run-N.csv và traces/ (file nộp)."""
    text = str(text)
    return text.replace(API_KEY, "[KEY]") if API_KEY else text


def _send(req, timeout):
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post_json(url, headers, body, timeout=60):
    """Gửi POST JSON, trả về JSON phản hồi. Chỉ dùng thư viện chuẩn (urllib) — theo docs/connect-model.md.

    Lỗi tạm thời (429, 408, 409, 5xx, timeout, mất mạng) thì chờ RETRY_WAITS rồi thử lại. Hết lượt thử vẫn ném
    RuntimeError để cột `error` ghi đúng. Lần gọi lỗi không có `usage` nên không tính token."""
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers=dict({"Content-Type": "application/json"}, **headers))
    for attempt in range(len(RETRY_WAITS) + 1):
        try:
            data = _send(req, timeout)
            break
        except urllib.error.HTTPError as e:
            with e:
                msg = "HTTP %d: %s" % (e.code, e.read().decode("utf-8", "replace")[:300])
            retry = e.code in RETRY_STATUS or e.code >= 500
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            msg = "%s: %s" % (type(e).__name__, getattr(e, "reason", e))
            retry = True
        if not retry or attempt == len(RETRY_WAITS):
            raise RuntimeError(mask_key(msg + ("" if attempt == 0 else " (sau %d lần gọi)" % (attempt + 1))))
        time.sleep(RETRY_WAITS[attempt])
    if SHOW_RAW:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    return data


def call_openai(system, user, model):
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    body = {"model": model, "messages": messages}
    if MODEL_MAX_TOKENS is not None:
        body["max_completion_tokens"] = MODEL_MAX_TOKENS   # tính cả token suy luận
    if MODEL_TEMPERATURE is not None:
        body["temperature"] = MODEL_TEMPERATURE
    data = post_json(URL_OPENAI, {"Authorization": "Bearer " + API_KEY}, body)
    # completion_tokens đã GỒM token suy luận (đã kiểm 27/11 với gpt-6-luna: 31 = 21 suy luận + 10 trả lời).
    u = data["usage"]
    return {"text": data["choices"][0]["message"].get("content") or "",
            "tokens_in": u["prompt_tokens"], "tokens_out": u["completion_tokens"]}


def call_claude(system, user, model):
    body = {"model": model, "max_tokens": MODEL_MAX_TOKENS or CLAUDE_DEFAULT_MAX_TOKENS, "system": system or "",
            "messages": [{"role": "user", "content": user}]}
    if MODEL_TEMPERATURE is not None:
        body["temperature"] = MODEL_TEMPERATURE
    data = post_json(URL_CLAUDE, {"x-api-key": API_KEY, "anthropic-version": "2023-06-01"}, body)
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    u = data["usage"]
    return {"text": text, "tokens_in": u["input_tokens"], "tokens_out": u["output_tokens"]}


PROVIDERS = {"openai": call_openai, "anthropic": call_claude}


@model_call
def call_model(system: str, user: str, model: str = None) -> dict:
    """model=None → MODEL_NAME. Trả đúng tên model đã gọi ở khoá "model" để simulate tính giá từng model."""
    if MODEL_PROVIDER == "fake":
        last = (user.strip().splitlines() or [""])[-1]
        return {"text": "[câu trả lời giả — chưa nối model] " + last[:60], "model": "fake", "tokens_in": 0, "tokens_out": 0}
    fn = PROVIDERS.get(MODEL_PROVIDER)
    if fn is None:
        raise NotImplementedError("MODEL_PROVIDER=%s chưa hỗ trợ trong codebase/ai.py (có: %s) — xem docs/connect-model.md"
                                  % (MODEL_PROVIDER, ", ".join(sorted(PROVIDERS))))
    model = model or MODEL_NAME
    if not model:
        raise RuntimeError("chưa điền MODEL_NAME trong .env")
    if not API_KEY:
        raise RuntimeError("chưa điền API_KEY trong .env")
    r = fn(system, user, model)
    return {"text": r["text"], "model": model, "tokens_in": int(r["tokens_in"]), "tokens_out": int(r["tokens_out"])}
