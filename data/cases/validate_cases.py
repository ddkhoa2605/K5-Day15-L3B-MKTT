# -*- coding: utf-8 -*-
"""Kiểm bộ nhãn data/cases/cases.jsonl — chỉ dùng thư viện chuẩn.

Chạy:  python data/cases/validate_cases.py [đường/dẫn/citations.json]
Thoát với mã 1 nếu có lỗi. Cảnh báo (WARN) không làm hỏng lượt kiểm.

Đây là kiểm TÍNH NHẤT QUÁN của nhãn (đủ trường, đúng enum, đúng phân bổ, mã căn cứ khớp
bảng quy ước trong LABELING.md §6, không có dữ liệu cá nhân thật). Nó KHÔNG sinh nhãn và
không thay thế việc người dán nhãn đọc từng case.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CASES = os.path.join(HERE, "cases.jsonl")
CORPUS = os.path.join(HERE, "corpus_cases.jsonl")  # tuỳ chọn: case data_that từ repo công khai
CORPUS_NGUON = re.compile(r"^data_that: corpus/repo-\d{2}$")
# Denylist ẩn danh (tên repo, tác giả, thương hiệu) — một từ mỗi dòng, để ở data/corpus/ (đã gitignore),
# KHÔNG commit vì chính danh sách này chứa định danh. Không có file thì bỏ qua bước này.
DENYLIST_FILE = os.path.join(ROOT, "data", "corpus", "denylist.txt")
DENYLIST = []
if os.path.exists(DENYLIST_FILE):
    with open(DENYLIST_FILE, encoding="utf-8") as _f:
        DENYLIST = [t.strip().lower() for t in _f if t.strip() and not t.startswith("#")]
# Tham số tuỳ chọn: đường dẫn citations.json khác (vd bản lấy từ nhánh chưa merge về máy).
CITATIONS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "legal", "citations.json")

INPUT_FIELDS = ["id", "mo_ta", "schema", "code", "loai_hinh", "so_chu_the_luy_ke"]
LABEL_FIELDS = ["nhom_kiem", "nhom_con", "C1", "C2", "C3", "nhom_nhay_cam", "can_cu",
                "can_cu_theo_nhom", "bang_chung", "ly_do", "do_kho", "tag", "split", "can_xac_nhan"]
ENUM = {
    "C1": {"KICH_HOAT", "KHONG_KICH_HOAT", "CAN_LUAT_SU"},
    "C2": {"KICH_HOAT", "KICH_HOAT_NANG", "KHONG_KICH_HOAT"},
    "C3": {"MAT_MIEN_TRU", "CON_MIEN_TRU", "KHONG_THUOC_DIEN_MIEN", "CAN_NGUOI_XAC_NHAN"},
    "loai_hinh": {"ho_kinh_doanh", "doanh_nghiep_sieu_nho", "doanh_nghiep_nho", "khoi_nghiep",
                  "doanh_nghiep_lon", "khong_ro"},
    "tag": {"ro", "vt", "am", "chatbox", "luy_ke", "tan_cong"},
    "split": {"dev", "holdout"},
    "do_kho": {"easy", "medium", "hard"},
}
DIEM = {"chung_toc_dan_toc": "a", "chinh_tri_ton_giao": "b", "doi_tu_rieng_tu": "c", "suc_khoe": "d",
        "sinh_trac_di_truyen": "đ", "tinh_duc": "e", "toi_pham": "g", "vi_tri_dinh_vi": "h",
        "dinh_danh_dien_tu": "i", "tai_chinh": "k", "hanh_vi_mang": "l"}
NHO = {"ho_kinh_doanh": ("Luat91 D38.3", "ND356 D41.2"), "doanh_nghiep_sieu_nho": ("Luat91 D38.3", "ND356 D41.2"),
       "doanh_nghiep_nho": ("Luat91 D38.2", "ND356 D41.1"), "khoi_nghiep": ("Luat91 D38.2", "ND356 D41.1")}
DISTRIBUTION = {"C1_chuyen_ra_ngoai": 8, "C1_api_khong_pii": 6, "C1_chatbox": 4, "C2_du": 5, "C2_thieu": 7,
                "C3_ro": 6, "C3_vt": 12, "C3_con_mien": 6, "C3_luy_ke": 6}
NGUONG = 100000
C2_KICH = {"Luat91 D9.3", "ND356 D6"}
KNOWN_CODES = ({"Luat91 D20.1", "Luat91 D20.2", "Luat91 D20.6", "Luat91 D9.4d", "ND356 D6.3"} | C2_KICH
               | {c for pair in NHO.values() for c in pair}
               | {"ND356 D4" + d for d in DIEM.values()})
FLAGS = {"XN%d" % i for i in range(1, 13)}

# Mẫu dữ liệu cá nhân thật / secret không được xuất hiện trong bộ nhãn.
PII_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}"),
    "sdt_vn": re.compile(r"(?<!\d)(?:\+?84|0)(?:3|5|7|8|9)\d{8}(?!\d)"),
    "cccd_12_so": re.compile(r"(?<!\d)\d{12}(?!\d)"),
    "so_the": re.compile(r"(?<!\d)(?:\d[ -]?){15,18}\d(?!\d)"),
    "api_key": re.compile(r"sk-[A-Za-z0-9]{10,}|AIza[0-9A-Za-z_-]{20,}|eyJ[A-Za-z0-9_-]{10,}\."),
}

errors, warns = [], []


def err(cid, msg):
    errors.append("%s: %s" % (cid, msg))


def warn(cid, msg):
    warns.append("%s: %s" % (cid, msg))


def expected_codes(n, lh):
    """Bảng quy ước LABELING.md §6 — dùng để KIỂM mã đã ghi, không để sinh trạng thái."""
    c1 = {"KICH_HOAT": ["Luat91 D20.1", "Luat91 D20.2"], "CAN_LUAT_SU": ["Luat91 D20.6"]}.get(n["C1"], [])
    c3 = []
    if n["C3"] == "MAT_MIEN_TRU":
        c3 = ["ND356 D4" + DIEM[c] for c in n["nhom_nhay_cam"]] + list(NHO[lh])
    elif n["C3"] == "CON_MIEN_TRU":
        c3 = list(NHO[lh])
    return set(c1), set(c3)


def main():
    rows = []
    with open(CASES, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as e:
                err("dòng %d" % i, "JSON hỏng: %s" % e)
    print("Số case: %d" % len(rows))
    if len(rows) != 60:
        err("tổng", "cần đúng 60 case, đang có %d" % len(rows))

    # Case dựng từ repo công khai (data_that): file riêng, không tính vào 60 case / phân bổ / split.
    if os.path.exists(CORPUS):
        with open(CORPUS, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    c = json.loads(line)
                except ValueError as e:
                    err("corpus dòng %d" % i, "JSON hỏng: %s" % e)
                    continue
                c["_corpus"] = True
                rows.append(c)
        print("Case corpus (data_that): %d" % sum(1 for r in rows if r.get("_corpus")))

    ids = [r.get("id") for r in rows]
    for d in sorted({x for x in ids if ids.count(x) > 1}):
        err(d, "id trùng")

    dist, splits, tags = {}, {}, {}
    holdout_kiem, holdout_traits = set(), set()
    for r in rows:
        cid = r.get("id", "?")
        for k in INPUT_FIELDS:
            if k not in r:
                err(cid, "thiếu trường input %s" % k)
        n = r.get("nhan") or {}
        for k in LABEL_FIELDS:
            if k not in n:
                err(cid, "thiếu trường nhãn %s" % k)
        if errors and errors[-1].startswith(cid + ": thiếu"):
            continue
        for k in ("C1", "C2", "C3", "tag", "split", "do_kho"):
            if n[k] not in ENUM[k]:
                err(cid, "%s=%r không thuộc enum" % (k, n[k]))
        if r["loai_hinh"] not in ENUM["loai_hinh"]:
            err(cid, "loai_hinh lạ %r" % r["loai_hinh"])
        lk = r["so_chu_the_luy_ke"]
        if lk is not None and not isinstance(lk, int):
            err(cid, "so_chu_the_luy_ke phải là số nguyên hoặc null")
        if not r["mo_ta"].strip() or not r["schema"]:
            err(cid, "mo_ta/schema rỗng")
        if not n["ly_do"].strip() or not n["bang_chung"]:
            err(cid, "thiếu ly_do hoặc bang_chung")
        for c in r["code"]:
            if set(c) != {"file", "line", "text"}:
                err(cid, "phần tử code phải có đúng file, line, text")
        for k in n["nhom_nhay_cam"]:
            if k not in DIEM:
                err(cid, "mã nhóm nhạy cảm lạ %r" % k)
        for fl in n["can_xac_nhan"]:
            if fl not in FLAGS:
                err(cid, "cờ xác nhận lạ %r" % fl)

        if r.get("_corpus"):
            # nguồn ghi đúng mã ẩn danh, không lộ tên/URL repo; corpus chỉ dùng cho dev/benchmark
            if not CORPUS_NGUON.match(n.get("nguon") or ""):
                err(cid, "case corpus cần nhan.nguon dạng 'data_that: corpus/repo-NN'")
            if n["split"] != "dev":
                err(cid, "case corpus phải là split dev")
            if not n["nhom_con"].endswith("_corpus"):
                err(cid, "case corpus cần nhom_con dạng '<C1|C2|C3>_corpus'")
            if n.get("nhom_con_goc") not in DISTRIBUTION:
                err(cid, "case corpus cần nhom_con_goc thuộc bảng phân bổ (để chạy cùng luật kiểm như 60 case)")
            row_text = json.dumps({k: v for k, v in r.items() if k != "_corpus"}, ensure_ascii=False)
            if re.search(r"github\.com|gitlab\.com|bitbucket\.org", row_text, re.I):
                err(cid, "case corpus không được ghi URL repo nguồn (dò trên toàn bộ dòng)")
            for term in DENYLIST:
                if term in row_text.lower():
                    err(cid, "case corpus chứa từ trong denylist cục bộ (tên repo/tác giả/thương hiệu)")
        else:
            dist[n["nhom_con"]] = dist.get(n["nhom_con"], 0) + 1
            splits[n["split"]] = splits.get(n["split"], 0) + 1
        tags[n["tag"]] = tags.get(n["tag"], 0) + 1
        if n["nhom_kiem"] != n["nhom_con"].split("_")[0]:
            err(cid, "nhom_kiem không khớp nhom_con")
        if n["split"] == "holdout":
            holdout_kiem.add(n["nhom_kiem"])
            if n["do_kho"] == "hard":
                holdout_traits.add("hard")
            if n["tag"] == "am":
                holdout_traits.add("am")
            if "CAN_LUAT_SU" in (n["C1"],) or n["C3"] == "CAN_NGUOI_XAC_NHAN":
                holdout_traits.add("can_ra_soat")

        # ---- căn cứ ----
        per = n["can_cu_theo_nhom"]
        union = []
        for g in ("C1", "C2", "C3"):
            for x in per.get(g, []):
                if x not in union:
                    union.append(x)
        if set(n["can_cu"]) != set(union) or len(n["can_cu"]) != len(set(n["can_cu"])):
            err(cid, "can_cu phải là hợp (không trùng) của can_cu_theo_nhom")
        for x in n["can_cu"]:
            if x not in KNOWN_CODES:
                err(cid, "mã căn cứ ngoài bảng quy ước: %r" % x)
        if n["C3"] in ("MAT_MIEN_TRU", "CON_MIEN_TRU") and r["loai_hinh"] not in NHO:
            err(cid, "C3=%s cần loai_hinh thuộc 4 nhóm Điều 38" % n["C3"])
        else:
            e1, e3 = expected_codes(n, r["loai_hinh"])
            if set(per["C1"]) != e1:
                err(cid, "can_cu C1 không khớp bảng quy ước")
            if set(per["C3"]) != e3:
                err(cid, "can_cu C3 không khớp bảng quy ước")
        c2 = set(per["C2"])
        if n["C2"] == "KHONG_KICH_HOAT" and c2:
            err(cid, "C2 KHONG_KICH_HOAT không được có căn cứ")
        if n["C2"] == "KICH_HOAT" and c2 != C2_KICH:
            err(cid, "C2 KICH_HOAT phải đúng là Luat91 D9.3 + ND356 D6")
        if n["C2"] == "KICH_HOAT_NANG":
            extra = c2 - C2_KICH
            if not C2_KICH <= c2 or not extra or not extra <= {"Luat91 D9.4d", "ND356 D6.3"}:
                err(cid, "C2 KICH_HOAT_NANG phải là Luat91 D9.3 + ND356 D6 + (Luat91 D9.4d và/hoặc ND356 D6.3)")

        # ---- nhất quán nhãn ↔ dữ liệu đầu vào ----
        cats = n["nhom_nhay_cam"]
        goc = n.get("nhom_con_goc") or n["nhom_con"]  # case corpus chạy cùng luật với nhóm con gốc
        if n["C3"] == "MAT_MIEN_TRU" and not cats and not (isinstance(lk, int) and lk >= NGUONG):
            err(cid, "MAT_MIEN_TRU nhưng không có nhóm nhạy cảm và chưa đạt ngưỡng")
        if n["C3"] == "CON_MIEN_TRU" and (cats or (isinstance(lk, int) and lk >= NGUONG)):
            err(cid, "CON_MIEN_TRU nhưng có nhóm nhạy cảm hoặc đạt ngưỡng")
        if n["C3"] in ("MAT_MIEN_TRU", "CON_MIEN_TRU") and lk is None:
            err(cid, "%s cần so_chu_the_luy_ke đã biết" % n["C3"])
        if n["C3"] == "KHONG_THUOC_DIEN_MIEN" and r["loai_hinh"] != "doanh_nghiep_lon":
            err(cid, "KHONG_THUOC_DIEN_MIEN chỉ dùng cho doanh_nghiep_lon")
        if r["loai_hinh"] == "doanh_nghiep_lon" and n["C3"] != "KHONG_THUOC_DIEN_MIEN":
            err(cid, "doanh_nghiep_lon phải là KHONG_THUOC_DIEN_MIEN")
        if (r["loai_hinh"] == "khong_ro" or lk is None) and n["C3"] in ("MAT_MIEN_TRU", "CON_MIEN_TRU"):
            err(cid, "thiếu loại hình/quy mô nhưng vẫn kết luận %s" % n["C3"])
        if goc == "C1_chatbox" and n["C1"] != "CAN_LUAT_SU":
            err(cid, "case chatbox phải là CAN_LUAT_SU")
        if n["C1"] in ("KICH_HOAT", "CAN_LUAT_SU") and not r["code"]:
            err(cid, "C1 %s cần code làm bằng chứng" % n["C1"])
        if goc == "C1_api_khong_pii" and n["C1"] != "KHONG_KICH_HOAT":
            err(cid, "nhóm API không kèm PII phải là KHONG_KICH_HOAT")
        if goc == "C2_du" and n["C2"] != "KHONG_KICH_HOAT":
            err(cid, "nhóm C2 đủ bằng chứng phải là KHONG_KICH_HOAT")
        if goc == "C2_thieu" and n["C2"] == "KHONG_KICH_HOAT":
            err(cid, "nhóm C2 thiếu bằng chứng không được là KHONG_KICH_HOAT")
        if goc in ("C3_ro", "C3_vt") and not cats:
            err(cid, "nhóm C3 nhạy cảm phải có nhom_nhay_cam")
        if goc == "C3_con_mien":
            # không nhạy cảm, dưới ngưỡng → CON_MIEN_TRU; riêng khi thiếu loại hình/quy mô thì CAN_NGUOI_XAC_NHAN
            unknown = r["loai_hinh"] == "khong_ro" or lk is None
            if cats or n["C3"] not in (("CAN_NGUOI_XAC_NHAN",) if unknown else ("CON_MIEN_TRU",)):
                err(cid, "nhóm không nhạy cảm/còn miễn trừ: cần nhom_nhay_cam rỗng và C3 = %s"
                    % ("CAN_NGUOI_XAC_NHAN" if unknown else "CON_MIEN_TRU"))
        if goc == "C3_luy_ke" and not (isinstance(lk, int) and lk >= NGUONG):
            err(cid, "nhóm lũy kế cần so_chu_the_luy_ke ≥ 100000")
        if n["tag"] == "vt" and goc != "C3_vt":
            warn(cid, "tag vt ngoài nhóm C3_vt")

        # ---- dữ liệu cá nhân thật / secret ----
        blob = json.dumps(r, ensure_ascii=False)
        for name, pat in PII_PATTERNS.items():
            for m in pat.findall(blob):
                if name == "cccd_12_so" or name == "so_the":
                    err(cid, "chuỗi số giống %s: %s" % (name, m))
                else:
                    err(cid, "phát hiện %s: %s" % (name, m))

    for k, v in DISTRIBUTION.items():
        if dist.get(k, 0) != v:
            err("phân bổ", "%s cần %d, đang %d" % (k, v, dist.get(k, 0)))
    for k in dist:
        if k not in DISTRIBUTION:
            err("phân bổ", "nhóm con lạ %s" % k)
    if splits.get("dev") != 50 or splits.get("holdout") != 10:
        err("split", "cần 50 dev / 10 holdout, đang %s" % splits)
    if holdout_kiem != {"C1", "C2", "C3"}:
        err("holdout", "phải có đủ C1, C2, C3 (đang %s)" % sorted(holdout_kiem))
    for t in ("hard", "am", "can_ra_soat"):
        if t not in holdout_traits:
            err("holdout", "thiếu case loại %s" % t)

    # ---- trùng kịch bản dev ↔ holdout ----
    # Độ giống = Jaccard trên tập từ của mo_ta + schema (so ký tự bằng difflib bị nhiễu bởi các câu
    # mẫu lặp lại như "Có bảng consents. Khoảng … người dùng" trên đoạn văn ngắn). Cộng thêm kiểm
    # schema hoặc code trùng hoàn toàn.
    def toks(r):
        return set(re.findall(r"\w+", (r["mo_ta"] + " " + " ".join(r["schema"])).lower()))

    dev = [r for r in rows if r["nhan"]["split"] == "dev"]
    hold = [r for r in rows if r["nhan"]["split"] == "holdout"]
    top = (0.0, "", "")
    for h in hold:
        for d in dev:
            th, td = toks(h), toks(d)
            j = len(th & td) / float(len(th | td) or 1)
            top = max(top, (j, h["id"], d["id"]))
            same_schema = sorted(h["schema"]) == sorted(d["schema"])
            same_code = bool(h["code"]) and [c["text"] for c in h["code"]] == [c["text"] for c in d["code"]]
            if j > 0.5 or same_schema or same_code:
                err(h["id"], "kịch bản quá giống %s (jaccard %.2f, schema trùng=%s, code trùng=%s)"
                    % (d["id"], j, same_schema, same_code))
    print("Độ giống dev↔holdout cao nhất: %.2f (%s ~ %s)" % top)

    # ---- luật sắt: mọi mã phải là khoá của data/legal/citations.json ----
    if os.path.exists(CITATIONS):
        with open(CITATIONS, encoding="utf-8") as f:
            cit = set(json.load(f))
        missing = sorted({x for r in rows for x in r["nhan"]["can_cu"]} - cit)
        if missing:
            err("citations.json", "mã không có trong %s: %s" % (CITATIONS, ", ".join(missing)))
        else:
            print("Đối chiếu citations.json: mọi mã đều có (%s)" % CITATIONS)
    else:
        warn("citations.json", "không thấy %s — chỉ đối chiếu với bảng quy ước trong LABELING.md" % CITATIONS)

    print("Phân bổ:", ", ".join("%s=%d" % (k, dist.get(k, 0)) for k in DISTRIBUTION))
    print("Split:", splits, "· Tag:", dict(sorted(tags.items())))
    for w in warns:
        print("WARN", w)
    for e in errors:
        print("LỖI", e)
    print("KẾT QUẢ:", "ĐẠT" if not errors else "KHÔNG ĐẠT (%d lỗi)" % len(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
