"""Task G2 bước 3–4 — quét tĩnh corpus và đếm số liệu cho evidence/data-mining.md.

Chạy:  python scripts/scan_corpus.py
       python scripts/scan_corpus.py --codebase <thư mục codebase khác>   # vd bản snapshot nhánh của Minh

Mỗi repo trong data/corpus/index.json:
  1. scanner.case_from_repo / find_sinks / find_consent (M2 của Minh) — phân tích tĩnh.
  2. agent.answer("repo:<đường dẫn>") ở chế độ SHP_MODE=rule, MODEL_PROVIDER=fake → không gọi model, không tốn token.
  3. Đọc khối ```json cuối của output → trạng thái C1/C2/C3 + nhóm dữ liệu nhạy cảm.

Output (KHÔNG commit, nằm trong data/corpus/):
  data/corpus/results.csv     ma, c1, c2, c3, nhom, … (một dòng một repo)
  data/corpus/summary.json    các tỉ lệ X/Y/Z + mẫu số, để chép sang evidence/data-mining.md
Chỉ in mã repo-NN, không in tên hay URL.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"

COLS = ["ma", "c1", "c2", "c3", "nhom", "so_bang", "so_cot", "so_sink", "loai_sink",
        "sink_ai", "co_bang_consent", "consent_du_3_truong", "tich_san", "im_lang_dong_y", "tin_hieu_ai", "loi"]


def last_json_block(text: str) -> dict:
    blocks = re.findall(r"```json\s*(.*?)```", text or "", re.S)
    for b in reversed(blocks):
        try:
            return json.loads(b)
        except ValueError:
            continue
    return {}


def pct(x: int, n: int) -> str:
    return f"{x}/{n} ({100 * x / n:.0f}%)" if n else "0/0"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--codebase", default=str(ROOT / "codebase"))
    args = ap.parse_args()

    os.environ["SHP_MODE"] = "rule"
    os.environ["MODEL_PROVIDER"] = "fake"
    sys.path.insert(0, str(Path(args.codebase).resolve()))
    import agent  # noqa: E402  (codebase của Minh)
    import scanner  # noqa: E402

    index = json.loads((CORPUS / "index.json").read_text(encoding="utf-8"))
    rows = []
    for e in index:
        path = CORPUS / e["ma"]
        row = {k: "" for k in COLS}
        row.update(ma=e["ma"], tin_hieu_ai=e.get("tin_hieu_ai", ""))
        if not path.is_dir():
            row["loi"] = "chua_clone"
            rows.append(row)
            continue
        try:
            files = scanner.load_repo(str(path))
            cols = scanner.repo_columns(files)
            sinks = scanner.find_sinks(files)
            consent = scanner.find_consent(files, cols)
            with redirect_stdout(io.StringIO()):
                out = agent.answer("repo:" + str(path))["output"]
            block = last_json_block(out)
            kq = block.get("ket_qua") or {}
            c3 = kq.get("C3") or {}
            row.update(
                c1=(kq.get("C1") or {}).get("trang_thai", ""),
                c2=(kq.get("C2") or {}).get("trang_thai", ""),
                c3=c3.get("trang_thai", ""),
                nhom="|".join(sorted(c3.get("nhom_nhay_cam") or [])),
                so_bang=len({c["table"] for c in cols}), so_cot=len(cols), so_sink=len(sinks),
                loai_sink="|".join(sorted({s["kind"] for s in sinks})),
                sink_ai=int(any(s["kind"] == "ai_nuoc_ngoai" for s in sinks)),
                co_bang_consent=int(bool(consent["bang_consent"])),
                consent_du_3_truong=int(bool(consent["du_3_truong"])),
                tich_san=len(consent["tich_san"]), im_lang_dong_y=len(consent["im_lang_dong_y"]),
                loi="tu_choi" if block.get("tu_choi") else ("" if block else "khong_co_json"),
            )
        except Exception as ex:  # noqa: BLE001 — một repo lỗi không dừng cả corpus
            row["loi"] = type(ex).__name__
        rows.append(row)
        print(f"  {row['ma']}: C1={row['c1'] or '-'} C2={row['c2'] or '-'} C3={row['c3'] or '-'} "
              f"nhom={row['nhom'] or '-'} sink={row['so_sink']} {row['loi']}")

    with (CORPUS / "results.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if not r["loi"]]
    n = len(ok)
    cnt = lambda pred: sum(1 for r in ok if pred(r))  # noqa: E731
    summary = {
        "ngay_quet": dt.date.today().isoformat(),
        "n_index": len(rows), "n_quet_duoc": n,
        "X_c1_kich_hoat": cnt(lambda r: r["c1"] == "KICH_HOAT"),
        "X2_c1_can_xem": cnt(lambda r: r["c1"] not in ("KICH_HOAT", "KHONG_KICH_HOAT", "")),
        "co_sink_ngoai": cnt(lambda r: int(r["so_sink"] or 0) > 0),
        "co_sink_ai": cnt(lambda r: r["sink_ai"] == 1),
        "Y_khong_nhat_ky_dong_y": cnt(lambda r: r["consent_du_3_truong"] != 1),
        "Y2_khong_co_bang_consent": cnt(lambda r: r["co_bang_consent"] != 1),
        "c2_kich_hoat": cnt(lambda r: str(r["c2"]).startswith("KICH_HOAT")),
        "Z_cham_nhay_cam": cnt(lambda r: bool(r["nhom"])),
        "c3_mat_mien_tru": cnt(lambda r: r["c3"] == "MAT_MIEN_TRU"),
        "c3_can_nguoi_xac_nhan": cnt(lambda r: r["c3"] == "CAN_NGUOI_XAC_NHAN"),
        "co_tin_hieu_ai": cnt(lambda r: bool(r["tin_hieu_ai"])),
        "nhom_dem": {},
        "trang_thai_dem": {k: {} for k in ("c1", "c2", "c3")},
    }
    for r in ok:
        for g in filter(None, r["nhom"].split("|")):
            summary["nhom_dem"][g] = summary["nhom_dem"].get(g, 0) + 1
        for k in ("c1", "c2", "c3"):
            summary["trang_thai_dem"][k][r[k]] = summary["trang_thai_dem"][k].get(r[k], 0) + 1
    (CORPUS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nQuét được {n}/{len(rows)} repo · ngày {summary['ngay_quet']}")
    print(f"  X  C1 = KICH_HOAT (gửi DLCN ra nước ngoài):   {pct(summary['X_c1_kich_hoat'], n)}")
    print(f"     có lời gọi ra ngoài bất kỳ / gọi AI:        {pct(summary['co_sink_ngoai'], n)} / {pct(summary['co_sink_ai'], n)}")
    print(f"  Y  không có nhật ký đồng ý đủ 3 trường:        {pct(summary['Y_khong_nhat_ky_dong_y'], n)}")
    print(f"     không có bảng consent nào:                  {pct(summary['Y2_khong_co_bang_consent'], n)}")
    print(f"  Z  chạm nhóm dữ liệu nhạy cảm:                 {pct(summary['Z_cham_nhay_cam'], n)}  {summary['nhom_dem']}")
    print(f"  Trạng thái: {summary['trang_thai_dem']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
