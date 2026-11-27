"""Rule engine (task M5): ra quyết định C1, C2, C3 và gắn căn cứ. KHÔNG gọi model.

Mọi mã căn cứ hoặc đọc từ data/legal/*.json, hoặc là hằng số dưới đây; mọi mã đi qua legal.cite()
(mã không có trong citations.json → KeyError, test bắt được). Model không bao giờ sinh mã điều luật.

Đầu vào:
  case    — Case (loai_hinh, so_chu_the_luy_ke…)
  labels  — kết quả phân loại cột: {"table", "column", "nhom", "do_tin_cay", ["file", "line"]}
  paths   — kết quả kiểm chứng sink: {"xac_nhan", "truong_ca_nhan", "nguon", "sink": {file, line, kind, endpoint, snippet}}
  consent — kết quả scanner.find_consent
"""
import legal

CONF_MIN = 0.7  # độ tin cậy tối thiểu để coi một cột thuộc nhóm đã phân loại

# Hằng số căn cứ (đã có trong citations.json — test_all_citations_exist kiểm)
C1_KICH_HOAT = ["Luat91 D20.1", "Luat91 D20.2"]
C1_CAN_LUAT_SU = ["Luat91 D20.6"]
C2_KICH_HOAT = ["Luat91 D9.3", "ND356 D6"]
C2_IM_LANG = "Luat91 D9.4d"
C2_TICH_SAN = "ND356 D6.3"

HAN_CHOT_C1 = "60 ngày kể từ lần chuyển dữ liệu đầu tiên"
PHAT_PREFIX = "Mức phạt tham khảo (khung tối đa theo Nghị định 330, không phải mức chắc chắn bị áp): "


def _checked(codes):
    out = []
    for c in codes:
        if c and c not in out:
            legal.cite(c)
            out.append(c)
    return out


def _finding(trang_thai, can_cu, giai_thich, bang_chung=None, han_chot=None, muc_phat=None, **extra):
    f = {"trang_thai": trang_thai, "can_cu": _checked(can_cu), "bang_chung": bang_chung or [],
         "han_chot": han_chot, "muc_phat": muc_phat, "giai_thich": giai_thich}
    f.update(extra)
    return f


def _penalty(*keys):
    """Mức phạt tham khảo của một hoặc nhiều mục trong penalties.json. Ghi rõ mức của tổ chức, mức cá nhân
    bằng một nửa. Mã Nghị định 330 chỉ nằm trong câu chữ, KHÔNG đưa vào can_cu (LABELING.md §6.3)."""
    parts = []
    for key in keys:
        p = legal.load()["penalties"].get(key)
        if not p:
            continue
        codes = [c for c in p.get("can_cu") or [] if c]
        for c in codes:
            legal.cite(c)
        s = "tổ chức " + p["muc"]
        if codes:
            s += " (%s)" % ", ".join(codes)
        if p.get("muc_ca_nhan"):
            s += "; cá nhân bằng một nửa: " + p["muc_ca_nhan"]
        parts.append(s)
    return PHAT_PREFIX + " · ".join(parts) if parts else None


def _col_evidence(labels):
    ev = []
    for l in labels:
        item = {"file": l.get("file"), "line": l.get("line"), "snippet": "%s.%s" % (l["table"], l["column"]),
                "nhom": l["nhom"], "do_tin_cay": l["do_tin_cay"]}
        ev.append(item)
    return ev


# ---------------------------------------------------------------- C3

def evaluate_c3(case, labels):
    data = legal.load()
    ex = data["exemption"]
    cats = data["categories"]
    sensitive = legal.sensitive_groups()
    loai_hinh = case.get("loai_hinh")
    if loai_hinh not in ex["loai_hinh"]:
        loai_hinh = "khong_ro"
    luy_ke = case.get("so_chu_the_luy_ke")
    if isinstance(luy_ke, bool) or not isinstance(luy_ke, int):
        luy_ke = None
    sure = [l for l in labels if l["nhom"] in sensitive and l["do_tin_cay"] >= CONF_MIN]
    unsure = [l for l in labels if l["nhom"] == "khong_ro"
              or (l["nhom"] in sensitive and l["do_tin_cay"] < CONF_MIN)]
    groups = sorted({l["nhom"] for l in sure})
    group_codes = [cats[g]["can_cu"] for g in groups]
    over = luy_ke is not None and luy_ke >= ex["nguong_luy_ke"]

    if loai_hinh == "doanh_nghiep_lon":
        return _finding("KHONG_THUOC_DIEN_MIEN", [],
                        "Doanh nghiệp lớn không thuộc diện được miễn Điều 21, 22, khoản 2 Điều 33 Luật 91.",
                        _col_evidence(sure), nhom_nhay_cam=groups)
    # Thứ tự theo data/cases/LABELING.md §C3: chưa rõ loại hình / quy mô đứng TRƯỚC dữ liệu nhạy cảm (XN8).
    if loai_hinh == "khong_ro" or luy_ke is None:
        if sure:
            why = ("Đã thấy dữ liệu nhạy cảm (%s) nhưng chưa biết loại hình doanh nghiệp / số chủ thể lũy kế. "
                   "Dù loại hình nào, kết luận đều là KHÔNG còn miễn trừ (mất miễn trừ, hoặc không thuộc diện được miễn); "
                   "cần xác nhận loại hình để chốt căn cứ." % ", ".join(groups))
        else:
            why = "Chưa có loại hình doanh nghiệp hoặc số chủ thể lũy kế; cần người xác nhận để biết còn miễn trừ không."
        return _finding("CAN_NGUOI_XAC_NHAN", [], why, _col_evidence(sure), nhom_nhay_cam=groups)
    lh = ex["loai_hinh"][loai_hinh]
    if sure or over:
        reasons = []
        if sure:
            reasons.append("trực tiếp xử lý dữ liệu nhạy cảm (%s)" % ", ".join(groups))
        if over:
            reasons.append("quy mô lũy kế %s chủ thể ≥ ngưỡng %s" % (luy_ke, ex["nguong_luy_ke"]))
        return _finding("MAT_MIEN_TRU", group_codes + [lh["can_cu"], lh["can_cu_nd"]],
                        "Mất miễn trừ vì " + " và ".join(reasons) + ". Nghĩa vụ Điều 21, 22, khoản 2 Điều 33 Luật 91 đã phát sinh.",
                        _col_evidence(sure), muc_phat=_penalty("C3"), nhom_nhay_cam=groups)
    if unsure:
        return _finding("CAN_NGUOI_XAC_NHAN", [],
                        "Có cột chưa xác định được nhóm dữ liệu (%s); cần người xác nhận trước khi kết luận miễn trừ."
                        % ", ".join("%s.%s" % (l["table"], l["column"]) for l in unsure[:8]),
                        _col_evidence(unsure), nhom_nhay_cam=groups)
    return _finding("CON_MIEN_TRU", [lh["can_cu"], lh["can_cu_nd"]],
                    "Không thấy dữ liệu nhạy cảm, quy mô dưới ngưỡng: còn miễn trừ theo loại hình %s." % loai_hinh,
                    nhom_nhay_cam=groups)


# ---------------------------------------------------------------- C1

def _sink_evidence(paths):
    ev = []
    for p in paths:
        s = p.get("sink") or {}
        ev.append({"file": s.get("file"), "line": s.get("line"), "snippet": s.get("dong") or s.get("endpoint"),
                   "dich": s.get("endpoint"), "truong_ca_nhan": p.get("truong_ca_nhan", [])})
    return ev


def evaluate_c1(paths):
    confirmed = [p for p in paths if p.get("xac_nhan")]
    system = [p for p in confirmed if p.get("nguon") == "he_thong"]
    if system:
        return _finding("KICH_HOAT", C1_KICH_HOAT,
                        "App tự gửi dữ liệu cá nhân sang dịch vụ ngoài lãnh thổ Việt Nam: nghĩa vụ lập hồ sơ đánh giá tác động chuyển dữ liệu xuyên biên giới đã phát sinh.",
                        _sink_evidence(system), han_chot=HAN_CHOT_C1, muc_phat=_penalty("C1"))
    other = [p for p in confirmed if p.get("nguon") in ("nguoi_dung_tu_nhap", "khong_ro")]
    if other:
        return _finding("CAN_LUAT_SU", C1_CAN_LUAT_SU,
                        "Dữ liệu gửi ra ngoài là chữ người dùng tự nhập hoặc chưa xác định được nguồn; có thể thuộc trường hợp không phải đánh giá tác động — cần luật sư xem.",
                        _sink_evidence(other))
    return _finding("KHONG_KICH_HOAT", [], "Không thấy đường đi mang dữ liệu cá nhân ra dịch vụ nước ngoài.",
                    _sink_evidence([p for p in paths if not p.get("xac_nhan")]))


# ---------------------------------------------------------------- C2

def evaluate_c2(labels, consent):
    sensitive = legal.sensitive_groups()
    personal = [l for l in labels if (l["nhom"] in sensitive or l["nhom"] == "pii_co_ban") and l["do_tin_cay"] >= CONF_MIN]
    silence, prechecked = consent.get("im_lang_dong_y") or [], consent.get("tich_san") or []
    if silence or prechecked:
        codes = list(C2_KICH_HOAT)
        why = []
        if silence:
            codes.append(C2_IM_LANG)
            why.append("coi việc tiếp tục sử dụng là đồng ý")
        if prechecked:
            codes.append(C2_TICH_SAN)
            why.append("ô đồng ý được tích sẵn")
        return _finding("KICH_HOAT_NANG", codes,
                        "Cách xin đồng ý không hợp lệ: " + " và ".join(why) + ".",
                        [{"file": l["file"], "line": l["line"], "snippet": l["snippet"]} for l in silence + prechecked],
                        muc_phat=_penalty(*((["C2_NANG"] if silence else []) + (["C2_NANG_TICH_SAN"] if prechecked else []))))
    if personal and not consent.get("du_3_truong"):
        table = consent.get("bang_consent")
        why = ("Bảng %s thiếu trường để chứng minh sự đồng ý (người dùng · thời điểm · phiên bản chính sách)." % table
               if table else "Không thấy bảng lưu nhật ký đồng ý.")
        return _finding("KICH_HOAT", C2_KICH_HOAT,
                        "App xử lý dữ liệu cá nhân nhưng chưa lưu được bằng chứng đồng ý. " + why,
                        _col_evidence(personal[:5]), muc_phat=_penalty("C2"))
    if consent.get("du_3_truong"):
        why = "Có bảng nhật ký đồng ý đủ 3 trường."
    elif any(l["nhom"] == "khong_ro" for l in labels):
        why = "Chưa xác định được cột nào là dữ liệu cá nhân (có cột chưa phân loại được) — xem C3."
    else:
        why = "Không thấy cột dữ liệu cá nhân."
    return _finding("KHONG_KICH_HOAT", [], why)


FREE_TEXT_NOTE = ("Cột chữ tự do (%s) có thể chứa dữ liệu nhạy cảm do người dùng tự nhập; hệ thống không đọc nội dung, "
                  "nên kết luận trên dựa vào thiết kế của app.")


def _free_text_note(c3, labels):
    """Quyết định của Khoa (28/11): cột chữ tự do không đổi trạng thái C3, nhưng luôn kèm một dòng nhắc."""
    import classify
    cols = ["%s.%s" % (l["table"], l["column"]) for l in labels
            if classify.is_free_text(l["column"]) and l["nhom"] not in legal.sensitive_groups()]
    if cols:
        c3["luu_y"] = FREE_TEXT_NOTE % ", ".join(cols[:5])
        c3["giai_thich"] += " " + c3["luu_y"]
    return c3


def evaluate(case: dict, labels: list, paths: list, consent: dict) -> dict:
    return {"C1": evaluate_c1(paths), "C2": evaluate_c2(labels, consent),
            "C3": _free_text_note(evaluate_c3(case, labels), labels)}
