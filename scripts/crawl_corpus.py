"""Task G2 bước 1–2 — tìm và tải corpus repo công khai Next.js + Supabase của người Việt.

Chạy:  python scripts/crawl_corpus.py               # tìm + clone tới khi đủ --target repo (mặc định 40)
       python scripts/crawl_corpus.py --target 50
       python scripts/crawl_corpus.py --dry-run     # chỉ tìm, in danh sách, không clone

Token GitHub (tuỳ chọn, để tăng giới hạn API): biến môi trường GITHUB_TOKEN, hoặc `gh auth token` nếu đã cài gh.
Không có token vẫn chạy được, nhưng Search API chỉ cho 10 lượt/phút → script tự chờ.

Output (KHÔNG commit, `data/corpus/` nằm trong .gitignore):
  data/corpus/index.json     [{"ma": "repo-01", "url": …, "tin_hieu_ai": …, "ngay_lay": …}, …]
  data/corpus/repo-NN/       bản clone --depth 1

Ranh giới: chỉ đọc mã nguồn công khai (GitHub API + git clone). Không gọi endpoint của app, không chạy app.
Mã repo-NN đã có trong index.json giữ nguyên số; repo mới được nối tiếp.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
INDEX = CORPUS / "index.json"
USER_AGENT = "ship-hop-phap-crawler"

# Chỉ chữ RIÊNG của tiếng Việt. Bỏ â/ê/ô: tiếng Pháp, Bồ Đào Nha cũng có → lần chạy đầu lọt app Brazil/Pháp.
VN = re.compile("[ăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", re.I)
VN_WORDS = re.compile(r"\b(vietnam|viet ?nam|vietnamese|vnpay|zalo|vietqr|ghn|ghtk)\b", re.I)
VN_MIN_FILES = 5  # sau khi clone: ≥5 file mã nguồn/README có chữ tiếng Việt (chuỗi giao diện thật)
AI_SIGNAL = re.compile(r"(lovable|bolt\.new|stackblitz|cursor|v0\.dev|windsurf|claude code|built with ai)", re.I)

# Chỉ dùng chữ không dấu: GitHub Search tách từ có dấu không ổn định. Lọc tiếng Việt làm sau.
QUERIES = [
    "supabase nextjs in:readme,description",
    "supabase next.js vietnam",
    "supabase nextjs vietnamese",
    "supabase nextjs quan ly",
    "supabase nextjs he thong",
    "supabase nextjs dat lich",
    "supabase nextjs khach hang",
    "supabase nextjs ban hang",
    "supabase zalo",
    "supabase vnpay",
    "supabase momo",
    "supabase vietqr",
    "lovable supabase vietnam",
    "supabase nextjs viet",
    "supabase nextjs tieng viet",
    "supabase nextjs shop vietnam",
    "supabase nextjs clinic",
    "supabase nextjs school vietnam",
    "supabase nextjs booking",
    "supabase nextjs crm",
]


# ---------------------------------------------------------------- HTTP

def _token() -> str | None:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok.strip()
    if shutil.which("gh"):
        try:
            out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
            return out.stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            return None
    return None


def _ssl_contexts():
    yield None
    try:
        import certifi  # có sẵn ở nhiều máy; không bắt buộc
        yield ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass


def http_get(url: str, token: str | None = None, raw: bool = False):
    headers = {"User-Agent": USER_AGENT}
    if not raw:
        headers["Accept"] = "application/vnd.github+json"
    if token and not raw:
        headers["Authorization"] = f"Bearer {token}"
    last = None
    for ctx in _ssl_contexts():
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30, context=ctx) as r:
                body = r.read()
                return body.decode("utf-8", "replace") if raw else json.loads(body)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, ssl.SSLError) as e:
            last = e
            continue
    raise last  # type: ignore[misc]


def search(query: str, token: str | None, page: int = 1) -> list[dict]:
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": query, "sort": "updated", "order": "desc", "per_page": 100, "page": page})
    for attempt in range(3):
        try:
            return http_get(url, token).get("items", [])
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                wait = 65
                print(f"  giới hạn Search API, chờ {wait}s…")
                time.sleep(wait)
                continue
            if e.code == 422:
                return []
            raise
    return []


def readme_text(full_name: str, branch: str) -> str:
    for name in ("README.md", "readme.md", "README.MD"):
        try:
            return http_get(f"https://raw.githubusercontent.com/{full_name}/{branch}/{name}", raw=True)[:20000]
        except Exception:  # noqa: BLE001
            continue
    return ""


# ---------------------------------------------------------------- lọc

def candidate(item: dict) -> bool:
    if item.get("fork") or item.get("archived"):
        return False
    if item.get("language") not in ("TypeScript", "JavaScript", None):
        return False
    if item.get("size", 0) > 200_000:  # KB; bỏ repo khổng lồ
        return False
    return True


def vn_signal(item: dict, readme: str) -> bool:
    text = " ".join([item.get("description") or "", item.get("full_name") or "", readme])
    return bool(VN.search(text) or VN_WORDS.search(text))


def has_schema(path: Path) -> bool:
    """Có schema Supabase: supabase/migrations/*.sql, hoặc file .sql có CREATE TABLE."""
    mig = path / "supabase" / "migrations"
    if mig.is_dir() and any(mig.glob("*.sql")):
        return True
    for p in path.rglob("*.sql"):
        if "node_modules" in p.parts:
            continue
        try:
            if re.search(r"create\s+table", p.read_text(encoding="utf-8", errors="ignore"), re.I):
                return True
        except OSError:
            continue
    return False


def vn_files(path: Path, stop: int = VN_MIN_FILES) -> int:
    """Đếm file (.md/.ts/.tsx/.js/.jsx/.json/.sql) có chữ tiếng Việt, dừng sớm khi đủ `stop`."""
    n = 0
    for p in path.rglob("*"):
        if p.suffix not in (".md", ".ts", ".tsx", ".js", ".jsx", ".json", ".sql") or "node_modules" in p.parts:
            continue
        try:
            if p.is_file() and VN.search(p.read_text(encoding="utf-8", errors="ignore")):
                n += 1
                if n >= stop:
                    break
        except OSError:
            continue
    return n


def is_nextjs(path: Path) -> bool:
    if any(path.glob("next.config.*")) or any(path.glob("*/next.config.*")):
        return True
    pkg = path / "package.json"
    try:
        return '"next"' in pkg.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def ai_signal_local(path: Path, readme: str) -> str:
    texts = [readme]
    for name in ("package.json", ".cursorrules", "README.md"):
        p = path / name
        if p.is_file():
            try:
                texts.append(p.read_text(encoding="utf-8", errors="ignore")[:20000])
            except OSError:
                pass
    if (path / ".cursor").exists() or (path / ".bolt").exists():
        texts.append("cursor")
    m = AI_SIGNAL.search(" ".join(texts))
    return m.group(1).lower() if m else ""


# ---------------------------------------------------------------- clone

def clone(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    r = subprocess.run(["git", "clone", "--depth", "1", "--single-branch", "--quiet", url, str(dest)],
                       capture_output=True, text=True, timeout=300,
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    return r.returncode == 0


def rm_tree(p: Path) -> None:
    def onerr(func, path, _):
        os.chmod(path, 0o700)
        func(path)
    shutil.rmtree(p, onerror=onerr)


# ---------------------------------------------------------------- main

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=40, help="số repo cần có trong corpus (30–50)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--recheck", action="store_true",
                    help="loại khỏi corpus các repo đã clone nhưng không đạt bộ lọc tiếng Việt hiện tại")
    args = ap.parse_args()

    CORPUS.mkdir(parents=True, exist_ok=True)
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else []
    rejected_file = CORPUS / "rejected.json"
    rejected = json.loads(rejected_file.read_text(encoding="utf-8")) if rejected_file.exists() else []
    if args.recheck:
        keep = []
        for e in index:
            d = CORPUS / e["ma"]
            if d.is_dir() and vn_files(d) < VN_MIN_FILES:
                rejected.append({**e, "ly_do": f"<{VN_MIN_FILES} file có chữ tiếng Việt"})
                rm_tree(d)
                print(f"  loại {e['ma']}: không đủ dấu hiệu tiếng Việt")
            else:
                keep.append(e)
        index = keep
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
        rejected_file.write_text(json.dumps(rejected, ensure_ascii=False, indent=1), encoding="utf-8")
    # URL đã loại cũng tính là "đã biết" để không clone lại; số repo-NN không dùng lại.
    known = {e["url"].rstrip("/").lower() for e in index + rejected}
    token = _token()
    print(f"Token GitHub: {'có' if token else 'không (Search API 10 lượt/phút)'} · đã có {len(index)} repo")

    # 1. Tìm ứng viên
    seen: dict[str, dict] = {}
    for q in QUERIES:
        items = search(q, token)
        new = [i for i in items if candidate(i) and i["html_url"].lower() not in known]
        for i in new:
            seen.setdefault(i["full_name"], i)
        print(f"  '{q}': {len(items)} kết quả, {len(new)} ứng viên mới (tổng {len(seen)})")
        if not token:
            time.sleep(7)
    # Ưu tiên repo cập nhật gần đây
    cands = sorted(seen.values(), key=lambda i: i.get("pushed_at") or "", reverse=True)
    print(f"Ứng viên chưa lọc tiếng Việt: {len(cands)}")

    # 2. Lọc tiếng Việt (README qua raw.githubusercontent, không tính vào giới hạn API) → clone → kiểm schema
    today = dt.date.today().isoformat()
    next_no = max([int(e["ma"].split("-")[1]) for e in index + rejected] or [0]) + 1
    added = 0
    for item in cands:
        if len(index) >= args.target:
            break
        readme = readme_text(item["full_name"], item.get("default_branch") or "main")
        if not vn_signal(item, readme):
            continue
        if args.dry_run:
            print(f"  [dry] {item['full_name']} · {item.get('description') or ''}"[:140])
            continue
        ma = f"repo-{next_no:02d}"
        dest = CORPUS / ma
        if not clone(item["clone_url"], dest):
            print(f"  bỏ {item['full_name']}: clone lỗi")
            continue
        if not (has_schema(dest) and is_nextjs(dest) and vn_files(dest) >= VN_MIN_FILES):
            rm_tree(dest)
            continue
        index.append({"ma": ma, "url": item["html_url"], "tin_hieu_ai": ai_signal_local(dest, readme),
                      "pushed_at": (item.get("pushed_at") or "")[:10], "ngay_lay": today})
        known.add(item["html_url"].lower())
        next_no += 1
        added += 1
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  + {ma}  (tín hiệu AI: {index[-1]['tin_hieu_ai'] or '—'})")

    # 3. Clone các repo đã có trong index mà chưa có trên đĩa (vd repo-01..05 chọn tay)
    if not args.dry_run:
        for e in index:
            d = CORPUS / e["ma"]
            if not d.exists() and not clone(e["url"] + ".git", d):
                print(f"  {e['ma']}: clone lỗi")

    print(f"\nThêm {added} repo · corpus có {len(index)} repo → {INDEX.relative_to(ROOT)}")
    if len(index) < 30:
        print("Chưa đủ 30 repo: thêm query vào QUERIES hoặc đặt GITHUB_TOKEN rồi chạy lại.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
