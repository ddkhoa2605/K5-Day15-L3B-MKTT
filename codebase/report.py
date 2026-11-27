"""In kết luận cho người đọc + một khối ```json ở cuối để chấm tự động (eval/grade.py đọc khối json CUỐI CÙNG).

Cách nói: "nghĩa vụ đã phát sinh". Không dùng "vi phạm", "chứng nhận tuân thủ", "giúp tránh bị phạt".
"""
import json

import legal

TEN = {"C1": "Chuyển dữ liệu cá nhân ra nước ngoài (Điều 20 Luật 91)",
       "C2": "Xin và lưu sự đồng ý (Điều 9 Luật 91, Điều 6 NĐ 356)",
       "C3": "Miễn trừ cho doanh nghiệp nhỏ, siêu nhỏ (Điều 38 Luật 91, Điều 41 NĐ 356)"}
DISCLAIMER = ("Kết quả là gợi ý từ phân tích tĩnh mã nguồn để người chịu trách nhiệm xác nhận, "
              "không phải ý kiến pháp lý và không phải xác nhận app đã đáp ứng đủ nghĩa vụ.")

FORMAT_HELP = """Mình chỉ kiểm được một app cụ thể, theo một trong hai dạng:
  1. repo:<đường dẫn thư mục>   vd  repo:data/demo_repos/repo_c
  2. Một dòng JSON mô tả hệ thống, vd
     {"mo_ta": "App đặt sân", "schema": ["users(id, email)", "bookings(id, user_id, vi_tri_gan_nhat)"],
      "code": [{"file": "app/api/chat/route.ts", "line": 12, "text": "await openai.chat.completions.create(...)"}],
      "loai_hinh": "doanh_nghiep_sieu_nho", "so_chu_the_luy_ke": 4200}
     loai_hinh: ho_kinh_doanh · doanh_nghiep_sieu_nho · doanh_nghiep_nho · khoi_nghiep · doanh_nghiep_lon · khong_ro"""


def _cite_short(code):
    try:
        return legal.cite(code).split(" — ", 1)[-1][:110]
    except KeyError:
        return "(mã không có trong bảng luật)"


def render(findings: dict, sent: list, refused: bool = False, message: str = "", mo_ta: str = "",
           extra: str = "", mode: str = "") -> str:
    out = []
    if refused:
        out.append("Không kiểm được yêu cầu này. " + (message or ""))
        out.append("")
        out.append(FORMAT_HELP)
    else:
        out.append("KIỂM TRA NGHĨA VỤ DỮ LIỆU CÁ NHÂN TRƯỚC PHÁT HÀNH" + (" — " + mo_ta if mo_ta else ""))
        out.append(DISCLAIMER)
        if message:
            out.append(message)
        for key in ("C1", "C2", "C3"):
            f = findings.get(key)
            if not f:
                continue
            out.append("")
            out.append("%s · %s: %s" % (key, TEN[key], f["trang_thai"]))
            out.append("   " + f["giai_thich"])
            for code in f["can_cu"]:
                out.append("   Căn cứ %s — %s" % (code, _cite_short(code)))
            for ev in f["bang_chung"][:5]:
                where = "%s:%s" % (ev.get("file"), ev.get("line")) if ev.get("file") else "(case)"
                out.append("   Bằng chứng %s — %s" % (where, ev.get("snippet") or ""))
            if f.get("han_chot"):
                out.append("   Hạn: " + f["han_chot"])
            if f.get("muc_phat"):
                out.append("   " + f["muc_phat"])
        out.append("")
        out.append("Đã gửi ra ngoài (model AI): " + ("; ".join(sent) if sent else "không gửi gì"))
        if extra:
            out.append("")
            out.append(extra)
    block = {"tu_choi": bool(refused), "ket_qua": {} if refused else findings, "da_gui_ra_ngoai": sent}
    if mode:
        block["che_do"] = mode
    out.append("")
    out.append("```json")
    out.append(json.dumps(block, ensure_ascii=False))
    out.append("```")
    return "\n".join(out)
