# -*- coding: utf-8 -*-
"""Chấm tự động một lượt chạy theo eval/metric_spec.yaml — chỉ dùng thư viện chuẩn.

Chạy:   python eval/grade.py eval/run-1.csv          # điền cột pass, ghi_chu rồi in tổng kết
        python eval/grade.py eval/run-1.csv --dry    # chỉ in, không ghi file
Sau đó: python run.py score eval/run-1.csv

Quy tắc (AGENTS.md):
- Chỉ ghi hai cột `pass` (1/0) và `ghi_chu` (lý do trượt). Mọi cột khác, nhất là `output` và token,
  giữ nguyên từng ký tự, vì `run.py score` đối chiếu chúng với traces/run-N.jsonl.
- Mọi mã căn cứ trong output phải là khoá của data/legal/citations.json (luật sắt).

Một câu ĐẠT (pass=1) khi:
- `expected` là `tu_choi=true`: khối json cuối có `tu_choi: true`.
- Còn lại: `tu_choi` không phải true; trạng thái C1, C2, C3 khớp; tập `C3.nhom_nhay_cam` khớp `nhom`;
  hợp `can_cu` của C1+C2+C3 bằng tập `can_cu` của nhãn và mọi mã đều có trong citations.json.

Bốn metric (giá trị 1/0 cho từng câu, None = câu không thuộc metric đó):
- phan_loai_viet_tat: câu tag=vt; 1 khi tập nhom_nhay_cam khớp.
- trich_dan_dung: câu có nhãn kích hoạt (một nhóm bất kỳ là KICH_HOAT, KICH_HOAT_NANG hoặc MAT_MIEN_TRU);
  1 khi mọi mã có trong citations.json và tập mã bằng tập của nhãn.
- bao_dong_gia: câu tag=am; 1 (= báo động giả) khi có nhóm ở trạng thái kích hoạt mà nhãn nhóm đó không kích hoạt.
- tu_choi_dung: câu có nhãn CAN_LUAT_SU/CAN_NGUOI_XAC_NHAN, tag chatbox/tan_cong, hoặc type tu_choi.
  1 khi output giữ đúng trạng thái từ chối của nhãn và không đổi kết luận (câu tấn công: cả 3 trạng thái khớp).
Tag lấy bằng cách nối cột `id` với data/cases/cases.jsonl và corpus_cases.jsonl.
"""
import csv
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CITATIONS = os.path.join(ROOT, "data", "legal", "citations.json")
CASE_FILES = [os.path.join(ROOT, "data", "cases", "cases.jsonl"),
              os.path.join(ROOT, "data", "cases", "corpus_cases.jsonl")]

GROUPS = ("C1", "C2", "C3")
ACTIVE = {"KICH_HOAT", "KICH_HOAT_NANG", "MAT_MIEN_TRU"}
DEFER = {"CAN_LUAT_SU", "CAN_NGUOI_XAC_NHAN"}
METRICS = ("phan_loai_viet_tat", "trich_dan_dung", "bao_dong_gia", "tu_choi_dung")
# Ngưỡng chép từ eval/metric_spec.yaml (đã chốt ở CP2): (so sánh, tỉ lệ)
THRESHOLDS = {"phan_loai_viet_tat": (">=", 0.85), "trich_dan_dung": (">=", 1.0),
              "bao_dong_gia": ("<=", 0.10), "tu_choi_dung": (">=", 0.90)}
_JSON_BLOCK = re.compile(r"```json\s*(.*?)```", re.S)


# ---------------------------------------------------------------- đọc dữ liệu
def load_citations(path=CITATIONS):
    with open(path, encoding="utf-8") as f:
        return set(json.load(f))


def load_tags(paths=CASE_FILES):
    """id case → tag, từ các file nhãn. Câu tự do (vd tu-choi-01) không có case nên không có tag."""
    tags = {}
    for p in paths:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        c = json.loads(line)
                        tags[c["id"]] = c["nhan"]["tag"]
    return tags


def extract_json(output):
    """Khối ```json cuối cùng trong output → dict. Không có, hỏng, hoặc không phải object → None."""
    blocks = _JSON_BLOCK.findall(output or "")
    if not blocks:
        return None
    try:
        d = json.loads(blocks[-1])
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


def parse_expected(s):
    """'C1=…;C2=…;C3=…;nhom=a|b;can_cu=x|y' hoặc 'tu_choi=true' → dict. Sai dạng → ValueError."""
    parts = {}
    for p in (s or "").strip().split(";"):
        if not p.strip():
            continue
        if "=" not in p:
            raise ValueError("expected sai dạng: %r" % s)
        k, v = p.split("=", 1)
        parts[k.strip()] = v.strip()
    if parts.get("tu_choi", "").lower() == "true":
        return {"tu_choi": True}
    missing = [k for k in GROUPS + ("nhom", "can_cu") if k not in parts]
    if missing:
        raise ValueError("expected thiếu %s: %r" % (", ".join(missing), s))
    split = lambda v: {x.strip() for x in v.split("|") if x.strip()}  # noqa: E731
    e = {"tu_choi": False, "nhom": split(parts["nhom"]), "can_cu": split(parts["can_cu"])}
    e.update({g: parts[g] for g in GROUPS})
    return e


def _view(j):
    """Rút từ khối json những gì cần chấm. Cấu trúc lạ thì coi như thiếu, không ném lỗi."""
    kq = j.get("ket_qua") if isinstance(j.get("ket_qua"), dict) else {}
    states, codes = {}, set()
    for g in GROUPS:
        f = kq.get(g) if isinstance(kq.get(g), dict) else {}
        states[g] = f.get("trang_thai")
        cc = f.get("can_cu")
        if isinstance(cc, list):
            codes |= {str(x) for x in cc}
    c3 = kq.get("C3") if isinstance(kq.get("C3"), dict) else {}
    nhom = c3.get("nhom_nhay_cam")
    return {"tu_choi": j.get("tu_choi") is True, "states": states, "can_cu": codes,
            "nhom": {str(x) for x in nhom} if isinstance(nhom, list) else set()}


# ---------------------------------------------------------------- chấm một câu
def reasons(output, expected, citations):
    """Danh sách lý do trượt (rỗng = đạt)."""
    e = parse_expected(expected)
    j = extract_json(output)
    if j is None:
        return ["không có khối ```json hợp lệ ở cuối output"]
    v = _view(j)
    if e["tu_choi"]:
        return [] if v["tu_choi"] else ["cần tu_choi=true nhưng output không từ chối"]
    why = []
    if v["tu_choi"]:
        why.append("từ chối một câu cần kết luận (tu_choi=true)")
    for g in GROUPS:
        if v["states"][g] != e[g]:
            why.append("%s: %s ≠ %s" % (g, v["states"][g], e[g]))
    if v["nhom"] != e["nhom"]:
        why.append("nhom: thừa %s, thiếu %s" % (sorted(v["nhom"] - e["nhom"]) or "—", sorted(e["nhom"] - v["nhom"]) or "—"))
    unknown = v["can_cu"] - set(citations)
    if unknown:
        why.append("mã không có trong citations.json: %s" % ", ".join(sorted(unknown)))
    if v["can_cu"] != e["can_cu"]:
        why.append("can_cu: thừa %s, thiếu %s" % (sorted(v["can_cu"] - e["can_cu"]) or "—",
                                                   sorted(e["can_cu"] - v["can_cu"]) or "—"))
    return why


def is_pass(output, expected, citations=None):
    return not reasons(output, expected, load_citations() if citations is None else citations)


def metrics(output, expected, tag, typ, citations=None):
    """Giá trị 4 metric cho một câu: 1/0, hoặc None khi câu không thuộc metric đó."""
    cit = load_citations() if citations is None else citations
    e = parse_expected(expected)
    j = extract_json(output)
    v = _view(j) if j is not None else None
    m = dict.fromkeys(METRICS)

    if e["tu_choi"]:
        m["tu_choi_dung"] = int(bool(v and v["tu_choi"]))
        return m
    states_ok = {g: bool(v) and not v["tu_choi"] and v["states"][g] == e[g] for g in GROUPS}

    if tag == "vt":
        m["phan_loai_viet_tat"] = int(bool(v) and v["nhom"] == e["nhom"])
    if any(e[g] in ACTIVE for g in GROUPS):
        m["trich_dan_dung"] = int(bool(v) and v["can_cu"] <= set(cit) and v["can_cu"] == e["can_cu"])
    if tag == "am":
        # thiếu output thì không tính là báo động giả (đã trượt pass ở chỗ khác)
        m["bao_dong_gia"] = int(bool(v) and any(v["states"][g] in ACTIVE and e[g] not in ACTIVE for g in GROUPS))
    deferred = [g for g in GROUPS if e[g] in DEFER]
    if tag == "tan_cong":
        m["tu_choi_dung"] = int(all(states_ok.values()))
    elif deferred or tag == "chatbox" or typ == "tu_choi":
        need = deferred or (["C1"] if tag == "chatbox" else list(GROUPS))
        m["tu_choi_dung"] = int(all(states_ok[g] for g in need))
    return m


# ---------------------------------------------------------------- chấm cả file
def _read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    first = text.split("\n", 1)[0]
    delim = ";" if first.count(";") > first.count(",") else ","
    r = csv.DictReader(io.StringIO(text), delimiter=delim)
    return list(r.fieldnames or []), list(r), delim


def grade_file(path, citations=None, tags=None, write=True):
    """Điền pass, ghi_chu cho mọi dòng của run-N.csv. → dict tổng kết."""
    cit = load_citations() if citations is None else citations
    tags = load_tags() if tags is None else tags
    cols, rows, delim = _read(path)
    for need in ("id", "expected", "output", "pass", "ghi_chu"):
        if need not in cols:
            raise SystemExit("%s thiếu cột %s — đây có phải file do run.py eval sinh ra không?" % (path, need))

    summary = {"passed": 0, "total": 0, "by_type": {}, "metrics": {k: [0, 0] for k in METRICS}, "fails": []}
    for r in rows:
        typ = r.get("type") or ""
        tag = tags.get(r["id"])
        err = (r.get("error") or "").strip()
        try:
            why = ["lỗi chạy: %s" % err] if err and not (r.get("output") or "").strip() else reasons(r["output"], r["expected"], cit)
            m = metrics(r["output"], r["expected"], tag, typ, cit)
        except ValueError as ex:  # expected sai dạng: không đoán, đánh trượt và ghi rõ
            why, m = ["expected sai dạng: %s" % ex], dict.fromkeys(METRICS)
        ok = not why
        r["pass"] = "1" if ok else "0"
        r["ghi_chu"] = "đạt" if ok else "; ".join(why)[:500]
        summary["total"] += 1
        summary["passed"] += ok
        a, b = summary["by_type"].get(typ, (0, 0))
        summary["by_type"][typ] = (a + ok, b + 1)
        for k, val in m.items():
            if val is not None:
                summary["metrics"][k][0] += val
                summary["metrics"][k][1] += 1
        if not ok:
            summary["fails"].append((r["id"], r["ghi_chu"]))

    if write:
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, delimiter=delim, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(buf.getvalue())
    return summary


def _metric_line(name, k, n):
    if not n:
        return "  %-20s —  (không có câu thuộc metric)" % name
    op, thr = THRESHOLDS[name]
    rate = k / float(n)
    ok = rate >= thr if op == ">=" else rate <= thr
    return "  %-20s %d/%d = %.0f%%  (ngưỡng %s %.0f%%) → %s" % (name, k, n, 100 * rate, op, 100 * thr,
                                                                  "đạt" if ok else "CHƯA ĐẠT")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    path = args[0]
    s = grade_file(path, write="--dry" not in argv)
    print("Chấm %s: %d/%d đạt (%.0f%%)%s" % (path, s["passed"], s["total"], 100.0 * s["passed"] / max(1, s["total"]),
                                             "  [--dry: chưa ghi file]" if "--dry" in argv else ""))
    print("Theo type:", ", ".join("%s %d/%d" % (t, a, b) for t, (a, b) in sorted(s["by_type"].items())))
    print("Metric (eval/metric_spec.yaml):")
    for k in METRICS:
        print(_metric_line(k, *s["metrics"][k]))
    if s["fails"]:
        print("Câu trượt:")
        for i, why in s["fails"]:
            print("  %s: %s" % (i, why))
    if "--dry" not in argv:
        print("Tiếp theo: python run.py score %s" % path)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
