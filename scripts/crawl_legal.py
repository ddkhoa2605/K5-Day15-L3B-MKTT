"""Task G1 — crawl và chunk văn bản luật dữ liệu cá nhân.

Chạy:  python -m pip install pypdf
       python scripts/crawl_legal.py

Output:
  data/legal/raw/{luat91,nd356,nd330}.txt   văn bản đã làm sạch (NFC, bỏ header/footer lặp)
  data/legal/chunks.jsonl                   mỗi dòng một khoản: van_ban, dieu, khoan, tieu_de, text
  data/legal/SOURCES.md                     URL, ngày tải, sha256 từng file

pypdf chỉ dùng ở script này, không dùng trong codebase/.
Không có tác động ra ngoài ngoài việc tải các trang công khai (GET).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import io
import json
import re
import sys
import unicodedata
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGAL = ROOT / "data" / "legal"
RAW = LEGAL / "raw"
USER_AGENT = "ship-hop-phap-crawler"

SOURCES = [
    {
        "key": "luat91",
        "van_ban": "Luat91",
        "ten": "Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15",
        "url": "https://vplsdms.vn/upload/post/L_91_2025_QH15.pdf",
        "kind": "pdf",
        "toan_van": True,
        "phai_co": [20, 21, 22, 33, 38],
    },
    {
        "key": "nd356",
        "van_ban": "ND356",
        "ten": "Nghị định 356/2025/NĐ-CP hướng dẫn Luật Bảo vệ dữ liệu cá nhân",
        "url": "https://luatvietnam.vn/dan-su/nghi-dinh-356-2025-nd-cp-quy-dinh-chi-tiet-luat-bao-ve-du-lieu-ca-nhan-422896-d1.html",
        "kind": "html",
        "toan_van": True,
        "phai_co": [4, 41],
    },
    {
        "key": "nd330",
        "van_ban": "ND330",
        "ten": "Nghị định 330/2026/NĐ-CP xử phạt VPHC về bảo vệ dữ liệu cá nhân (bản tin EY)",
        "url": "https://www.ey.com/content/dam/ey-unified-site/ey-com/vi-vn/technical/tax/documents/ey-vn-decree-330-providing-sanctions-for-personal-data-protection.pdf",
        "kind": "pdf",
        "toan_van": False,  # bản tin tóm tắt của EY, KHÔNG phải toàn văn
        "phai_co": [],
    },
]

RE_DIEU = re.compile(r"^Điều\s+(\d+)\s*\.\s*(.*)$")
RE_KHOAN = re.compile(r"^(\d+)\s*\.\s+(.*)$")
RE_CHUONG = re.compile(r"^Chương\s+[IVXLC]+\b", re.I)
RE_MUC = re.compile(r"^Mục\s+\d+\b")
RE_PAGE_NO = re.compile(r"^(trang\s*)?\d{1,3}(\s*/\s*\d{1,3})?$", re.I)
END_MARKERS = ("Nơi nhận", "TM. CHÍNH PHỦ", "TM. QUỐC HỘI", "CHỦ TỊCH QUỐC HỘI",
               "- Ban Bí thư",  # bản HTML ND356 không có dòng "Nơi nhận", danh sách bắt đầu thẳng
               "Luật này được Quốc hội")


# ---------- tải ----------
def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


# ---------- trích text ----------
def pdf_to_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Thiếu pypdf. Chạy: python -m pip install pypdf")
    reader = PdfReader(io.BytesIO(data))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages)


class _TextExtractor(HTMLParser):
    BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "section", "article"}
    SKIP = {"script", "style", "noscript", "head", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_to_text(data: bytes) -> str:
    p = _TextExtractor()
    p.feed(data.decode("utf-8", errors="ignore"))
    return html.unescape("".join(p.out))


# ---------- làm sạch ----------
def normalize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).replace("\xa0", " ")
    # Font PDF tiếng Việt hay map "ư/Ư" thành "ƣ/Ƣ" (U+01A3/U+01A2) — không có trong tiếng Việt.
    text = text.replace("ƣ", "ư").replace("Ƣ", "Ư")
    lines = [re.sub(r"[ \t​]+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not RE_PAGE_NO.match(ln)]
    # Bỏ header/footer lặp: dòng ngắn xuất hiện >= 3 lần, không phải đầu điều/khoản.
    counts = Counter(lines)
    repeated = {
        ln for ln, c in counts.items()
        if c >= 3 and len(ln) < 80 and not RE_DIEU.match(ln) and not RE_KHOAN.match(ln)
    }
    return [ln for ln in lines if ln not in repeated]


def body_only(lines: list[str]) -> list[str]:
    """Cắt phần thân văn bản: từ 'Điều 1.' đến trước phần ký/nơi nhận.
    Cần cho trang HTML có menu, quảng cáo, bài liên quan xung quanh."""
    start = next((i for i, ln in enumerate(lines) if re.match(r"^Điều\s+1\s*\.", ln)), None)
    if start is None:
        return lines
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith(END_MARKERS):
            end = i
            break
    return lines[start:end]


# ---------- chunk ----------
def chunk(van_ban: str, lines: list[str]) -> list[dict]:
    """Tách theo Điều rồi theo khoản. Số điều/khoản phải tăng đúng 1 đơn vị,
    để dòng bị ngắt giữa câu (vd '20. ...' do PDF xuống dòng) không bị nhận nhầm."""
    chunks: list[dict] = []
    dieu = None
    tieu_de = ""
    khoan = None
    buf: list[str] = []

    def flush():
        if dieu is not None and buf:
            chunks.append({
                "van_ban": van_ban, "dieu": dieu, "khoan": khoan,
                "tieu_de": tieu_de, "text": " ".join(buf).strip(),
            })

    for ln in lines:
        m = RE_DIEU.match(ln)
        if m and (dieu is None or int(m.group(1)) == dieu + 1):
            flush()
            dieu, tieu_de, khoan, buf = int(m.group(1)), m.group(2).strip(), None, []
            continue
        if dieu is None:
            continue
        if RE_CHUONG.match(ln) or RE_MUC.match(ln):
            continue
        k = RE_KHOAN.match(ln)
        if k and int(k.group(1)) == (khoan or 0) + 1:
            flush()
            khoan, buf = int(k.group(1)), [ln]
            continue
        # Tiêu đề điều bị PDF ngắt sang dòng sau (chưa có nội dung, chưa có khoản)
        if khoan is None and not buf and tieu_de and not tieu_de.endswith((".", ":")) and len(ln) < 120 \
                and ln[:1].islower():
            tieu_de = f"{tieu_de} {ln}"
            continue
        buf.append(ln)
    flush()
    return chunks


def chunk_ban_tin(van_ban: str, lines: list[str], max_chars: int = 1200) -> list[dict]:
    """Văn bản không có cấu trúc Điều (bản tin): gom đoạn ~max_chars, dieu/khoan = None."""
    chunks, buf = [], []
    for ln in lines:
        buf.append(ln)
        if sum(len(x) for x in buf) >= max_chars:
            chunks.append(" ".join(buf))
            buf = []
    if buf:
        chunks.append(" ".join(buf))
    return [{"van_ban": van_ban, "dieu": None, "khoan": None, "tieu_de": "(bản tin, không phải toàn văn)",
             "text": t} for t in chunks]


# ---------- main ----------
def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    RAW.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    all_chunks: list[dict] = []
    rows: list[dict] = []
    ok = True

    for src in SOURCES:
        print(f"→ {src['van_ban']}: tải {src['url']}")
        try:
            data = fetch(src["url"])
        except Exception as e:  # noqa: BLE001
            print(f"  LỖI tải: {e}")
            ok = False
            continue
        text = pdf_to_text(data) if src["kind"] == "pdf" else html_to_text(data)
        lines = normalize(text)
        if src["toan_van"]:
            lines = body_only(lines)
            chunks = chunk(src["van_ban"], lines)
        else:  # bản tin: không tách theo Điều, tránh nhận nhầm số điều trích dẫn trong bài
            chunks = chunk_ban_tin(src["van_ban"], lines)

        txt = "\n".join(lines) + "\n"
        (RAW / f"{src['key']}.txt").write_text(txt, encoding="utf-8")
        all_chunks.extend(chunks)

        dieus = sorted({c["dieu"] for c in chunks if c["dieu"] is not None})
        missing = [d for d in src["phai_co"] if d not in dieus]
        print(f"  {len(dieus)} điều, {len(chunks)} chunk" + (f" (Điều {dieus[0]}–{dieus[-1]})" if dieus else ""))
        if missing:
            print(f"  THIẾU điều bắt buộc: {missing}")
            ok = False
        rows.append({
            **src, "ngay_tai": today,
            "sha256_goc": hashlib.sha256(data).hexdigest(),
            "sha256_txt": hashlib.sha256(txt.encode("utf-8")).hexdigest(),
            "so_dieu": len(dieus), "so_chunk": len(chunks),
        })

    with (LEGAL / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    write_sources(rows)
    print(f"\nĐã ghi {len(all_chunks)} chunk → {(LEGAL / 'chunks.jsonl').relative_to(ROOT)}")
    print("Việc tay: mở chunks.jsonl, so Luat91 Điều 20 khoản 6 với bản PDF.")
    return 0 if ok else 1


def write_sources(rows: list[dict]) -> None:
    out = [
        "# Nguồn văn bản luật (Task G1)",
        "",
        "Sinh bởi `python scripts/crawl_legal.py`. Chỉ tải trang công khai bằng GET, User-Agent `ship-hop-phap-crawler`.",
        "`sha256_goc` là hash của file tải về (PDF/HTML), `sha256_txt` là hash của `raw/<key>.txt` sau khi làm sạch.",
        "",
        "| Văn bản | Tên | URL | Loại | Toàn văn? | Ngày tải | Số điều | sha256_goc | sha256_txt |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| {r['van_ban']} | {r['ten']} | {r['url']} | {r['kind']} | {'có' if r['toan_van'] else '**không**'} "
            f"| {r['ngay_tai']} | {r['so_dieu']} | `{r['sha256_goc']}` | `{r['sha256_txt']}` |"
        )
    out += [
        "",
        "## Lưu ý",
        "",
        "- **ND330 chỉ là bản tin tóm tắt của EY, không phải toàn văn Nghị định 330/2026/NĐ-CP.** "
        "Mã điều khoản ND330 trong `citations.json` phải đối chiếu văn bản gốc; chưa có thì để `can_cu: []`, không đoán.",
        "- ND356 lấy từ bản HTML của luatvietnam.vn (bản sao trình bày lại, không phải Công báo). "
        "Trang wincolaw không tìm được; thuvienphapluat.vn chặn tải tự động (403).",
        "- Luật 91 lấy từ PDF do vplsdms.vn đăng lại.",
        "- Text trích tự động (pypdf/html.parser) có thể lỗi ngắt dòng. PDF Luật 91 còn ~20 chỗ chữ bị tách "
        "(vd `khô ng`, `liệ u`) do pypdf; không sửa tự động để tránh làm hỏng từ đúng. "
        "Điều khoản dùng làm căn cứ cần so tay với bản gốc.",
        "",
    ]
    (LEGAL / "SOURCES.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
