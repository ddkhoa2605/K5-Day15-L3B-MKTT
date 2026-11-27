"""Nạp bảng luật từ data/legal/*.json (Khoa dựng, task K1). Chỉ đọc, không tác động ra ngoài.

Luật sắt: mọi mã trích dẫn trong output phải là khoá có trong citations.json.
Mã trích dẫn là chuỗi nguyên văn (vd "ND356 D4đ") — KHÔNG đưa mã qua normalize().
"""
import json
import os
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGAL_DIR = os.path.join(ROOT, "data", "legal")
FILES = {
    "categories": "sensitive_categories.json",
    "exemption": "exemption.json",
    "citations": "citations.json",
    "penalties": "penalties.json",
}
NON_SENSITIVE = {"pii_co_ban", "khong_ca_nhan", "khong_ro"}

_cache = {}


def load() -> dict:
    """Đọc 4 bảng luật một lần, cache trong module."""
    if not _cache:
        for key, name in FILES.items():
            with open(os.path.join(LEGAL_DIR, name), encoding="utf-8") as f:
                _cache[key] = json.load(f)
    return _cache


def cite(code: str) -> str:
    """Mô tả của một mã trích dẫn. Ném KeyError nếu mã không có trong bảng."""
    citations = load()["citations"]
    if code not in citations:
        raise KeyError("mã trích dẫn không có trong citations.json: %r" % code)
    return citations[code]


def all_citation_codes() -> set:
    return set(load()["citations"])


def sensitive_groups() -> set:
    """Các mã nhóm dữ liệu nhạy cảm (có căn cứ ở ND356 Điều 4)."""
    return {k for k, v in load()["categories"].items() if v.get("can_cu") and k not in NON_SENSITIVE}


def known_groups() -> set:
    """Mọi mã nhóm hợp lệ cho bước phân loại cột."""
    return set(load()["categories"]) | {"khong_ca_nhan"}


def normalize(name: str) -> str:
    """Chuẩn hoá TÊN CỘT/BẢNG để so khớp: bỏ dấu, đ→d, chữ thường, bỏ ngoặc kép / backtick, bỏ khoảng trắng hai đầu."""
    s = (name or "").strip().strip('"`\'').replace('"', "").replace("`", "")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")
    return s.lower().strip()
