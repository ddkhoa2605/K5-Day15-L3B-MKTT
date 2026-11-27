"""Công cụ của bài toán — mỗi công cụ một hàm @tool (khung tự ghi vào trace). Khớp bảng công cụ ở spec.md §4.

| Công cụ            | Input                                   | Output                                 | Tác động ra ngoài? |
|--------------------|-----------------------------------------|----------------------------------------|--------------------|
| scan_repo          | đường dẫn repo                          | ngữ cảnh: case, files, cột, sink, consent | Không (chỉ đọc đĩa) |
| scan_case          | Case JSON                               | ngữ cảnh như trên                      | Không              |
| classify_columns   | cột, mô tả app, chế độ                  | nhóm dữ liệu + độ tin cậy mỗi cột      | Gửi TÊN CỘT ra model (chế độ hybrid) |
| verify_paths       | sink, cột cá nhân, chế độ               | đường đi có mang dữ liệu cá nhân không | Gửi đoạn code ĐÃ LỌC SECRET ra model (hybrid) |
| apply_rules        | case, nhãn cột, đường đi, consent       | C1/C2/C3 + căn cứ + bằng chứng         | Không              |
| draft_dpia         | kết luận                                | BẢN NHÁP hồ sơ (markdown)              | Không — không gửi, không nộp; người chịu trách nhiệm duyệt |
"""
import classify
import rules
import scanner
import verify
from tracing import tool, TOOLS  # noqa: F401

MAX_STEPS = 5  # số sink tối đa gửi model kiểm chứng trong một lần quét


def _line_of(files, path, line):
    lines = (files.get(path) or "").split("\n")
    return lines[line - 1].strip()[:200] if 1 <= line <= len(lines) else ""


def _context(case, files, columns):
    sinks = scanner.find_sinks(files)
    for s in sinks:
        s["dong"] = scanner.redact(_line_of(files, s["file"], s["line"]))
    return {"case": case, "files": files, "columns": columns, "sinks": sinks,
            "consent": scanner.find_consent(files, columns)}


@tool
def scan_repo(path: str) -> dict:
    """scan_repo · input: đường dẫn thư mục repo · output: ngữ cảnh {case, files, columns, sinks, consent}
    (cột kèm file + dòng). Chỉ đọc mã nguồn, không chạy app, không gọi endpoint. Không tác động ra ngoài."""
    files = scanner.load_repo(path)
    columns = scanner.repo_columns(files)
    case = scanner.case_from_repo(path)
    return _context(case, files, columns)


@tool
def scan_case(case: dict) -> dict:
    """scan_case · input: Case JSON (mo_ta, schema, code, loai_hinh, so_chu_the_luy_ke) · output: ngữ cảnh như scan_repo.
    Không tác động ra ngoài."""
    return _context(case, scanner.files_from_case(case), scanner.columns_from_case(case))


@tool
def classify_columns(columns: list, mo_ta: str, mode: str) -> list:
    """classify_columns · input: cột, mô tả app, chế độ (rule | hybrid) · output: [{table, column, nhom, do_tin_cay}].
    rule: so từ khoá, không gọi model. hybrid: 1 lần gọi model, chỉ gửi tên bảng / tên cột / mô tả. Không ghi dữ liệu."""
    labels = classify.classify_rule(columns) if mode == "rule" else classify.classify_llm(columns, mo_ta)
    for lab, col in zip(labels, columns):
        lab["file"], lab["line"] = col.get("file"), col.get("line")
    return labels


@tool
def verify_paths(sinks: list, pii_columns: list, mode: str) -> list:
    """verify_paths · input: sink, cột cá nhân, chế độ · output: [{xac_nhan, truong_ca_nhan, nguon, sink}].
    rule: sink nhắc tên cột cá nhân → hệ thống gửi. hybrid: hỏi model từng sink (tối đa MAX_STEPS), đoạn code đã lọc secret.
    Không ghi dữ liệu."""
    out = []
    for s in (sinks if mode == "rule" else sinks[:MAX_STEPS]):  # rule không gọi model → kiểm mọi sink
        if mode == "rule":
            res = verify.verify_path_rule(s, pii_columns)
        else:
            res = verify.verify_path_llm(s, pii_columns)
        res["sink"] = s
        out.append(res)
    return out


@tool
def apply_rules(case: dict, labels: list, paths: list, consent: dict) -> dict:
    """apply_rules · input: case, nhãn cột, đường đi, consent · output: {C1, C2, C3} mỗi cái có trang_thai, can_cu,
    bang_chung, han_chot, muc_phat, giai_thich. Chạy bằng code, không gọi model; mã căn cứ chỉ lấy từ data/legal. Không tác động ra ngoài."""
    return rules.evaluate(case, labels, paths, consent)


@tool
def draft_dpia(findings: dict) -> str:
    """draft_dpia · input: kết luận C1/C2/C3 · output: BẢN NHÁP markdown hồ sơ đánh giá tác động.
    KHÔNG gửi, KHÔNG nộp lên đâu cả — người chịu trách nhiệm duyệt và tự nộp."""
    lines = ["BẢN NHÁP — chờ người chịu trách nhiệm duyệt. Không phải hồ sơ đã nộp.", ""]
    c1 = findings.get("C1", {})
    if c1.get("trang_thai") == "KICH_HOAT":
        lines.append("## Hồ sơ đánh giá tác động chuyển dữ liệu xuyên biên giới (%s)" % ", ".join(c1["can_cu"]))
        for ev in c1.get("bang_chung", []):
            lines.append("- Dòng chuyển: `%s:%s` → %s · trường: %s"
                         % (ev.get("file"), ev.get("line"), ev.get("dich"), ", ".join(ev.get("truong_ca_nhan") or []) or "__"))
        lines += ["- Mục đích chuyển: __", "- Bên nhận, quốc gia: __", "- Biện pháp bảo vệ: __",
                  "- Hạn gửi: %s" % c1.get("han_chot"), ""]
    c3 = findings.get("C3", {})
    if c3.get("trang_thai") in ("MAT_MIEN_TRU", "KHONG_THUOC_DIEN_MIEN"):
        lines.append("## Hồ sơ đánh giá tác động xử lý dữ liệu cá nhân (Luat91 D21)")
        lines.append("- Nhóm dữ liệu nhạy cảm: %s" % (", ".join(c3.get("nhom_nhay_cam") or []) or "không"))
        lines += ["- Mục đích xử lý: __", "- Thời gian lưu: __", ""]
    if len(lines) == 2:
        lines.append("Không có nghĩa vụ lập hồ sơ nào được xác định là đã phát sinh.")
    return "\n".join(lines)
