# Tổng hợp bằng chứng pain

> Bản đầu cho **CP2 (19:30 Thứ Sáu 27/11)**, bản đủ trước **CP3 10:00 Thứ Bảy 28/11**. Chấm ở rubric R1.
> Người viết: Thắng (G3). Giả thuyết: `evidence/hypothesis.md` (có từ 16:46 27/11 trong canvas; file viết lúc 22:19, ghi rõ thời điểm).
> **Trạng thái (27/11 đêm):** đào data corpus **N = 35 repo** đã xong, có cách đếm chạy lại được và ≥5 ví dụ → nguồn đạt ngưỡng đầu tiên. Phỏng vấn chưa có.

## 0. Bốn pain mà `eval/metric_spec.yaml` trỏ về

Các trường `why` trong `metric_spec.yaml` (đã chốt ở CP2) trỏ về các pain dưới đây. Mỗi pain ghi bằng chứng hiện có và bằng chứng còn thiếu.

| # | Pain (không có chữ AI) | Metric trỏ về | Bằng chứng hiện có | Còn thiếu |
|---|---|---|---|---|
| P-a | **Không biết app đã kích hoạt nghĩa vụ nào**: freelancer đặt tên cột kiểu `tt_sk`, `vi_tri_gan_nhat`, gửi dữ liệu người dùng sang dịch vụ nước ngoài mà không nhận ra đó là chuyển dữ liệu xuyên biên giới | `phan_loai_viet_tat` | Corpus (mục 2.2): 32/35 repo lưu dữ liệu cá nhân cơ bản, 32/35 không có chỗ lưu sự đồng ý; 11/35 gọi AI nước ngoài. Bộ quét tự động gắn nhầm 6/9 cờ "nhạy cảm" → tên cột thật khó phân loại. Số nền B1, B4 | Phỏng vấn xác nhận "không biết" |
| P-b | **Bị khách hoặc nhà đầu tư hỏi mà không trả lời được**: không chỉ ra được căn cứ điều khoản nào, dòng code nào | `trich_dan_dung` | Chưa có số | Phỏng vấn: số lần bị hỏi / tháng, lần gần nhất mất bao lâu |
| P-c | **Tốn thời gian tra cứu cho cả những app không cần**: không biết app nào còn được miễn trừ (ND356 Điều 41) | `bao_dong_gia` | Chưa có bằng chứng cho pain "tốn thời gian". Bối cảnh từ corpus (không phải bằng chứng pain): sau kiểm tay chỉ 2/35 repo chạm dữ liệu nhạy cảm và 1/35 chắc chắn gửi dữ liệu cá nhân ra nước ngoài → nhiều app **không** kích hoạt C1/C3-nhạy cảm, nên công cụ cần phân biệt được thay vì báo đỏ đồng loạt | Phỏng vấn: phút tra cứu / app (bằng chứng thật cho P-c) |
| P-d | **Hậu quả khi không biết nghĩa vụ**: mức phạt tối đa theo ND330 và Luật 91; hồ sơ nộp sai phải làm lại | `tu_choi_dung` | B4 (mục 2.1); mức phạt tối đa theo `data/legal/penalties.json` của Khoa | Nguồn gốc của B4 |

## 1. Nguồn đã dùng

| Nguồn | Đạt ngưỡng? | File |
|---|---|---|
| Đào data: corpus repo công khai Next.js + Supabase (x/N, %, cách đếm chạy lại được, ≥5 ví dụ) | ☑ N = 35, 10 ví dụ, script `scripts/crawl_corpus.py` + `scan_corpus.py` | `evidence/data-mining.md` |
| Phỏng vấn (≥3 freelancer/agency dựng app cho SME, ngoài nhóm) | ☐ chưa hẹn | `evidence/interviews/P1.md`… |
| Khảo sát (≥20 người) | ☐ không dự kiến | — |
| Nghiên cứu bàn giấy (số nền, không thay được bằng chứng của nhóm) | — | mục 2.1 dưới đây |

## 2. Số chính

### 2.1 Số nền từ nghiên cứu gốc

Các số này cho thấy app dựng nhanh bằng AI thường xử lý dữ liệu cá nhân thiếu cẩn thận. Phần lớn là số về **bảo mật**, không phải về **nghĩa vụ pháp lý**, nên chỉ dùng làm bối cảnh cho P-a. Bảo mật kỹ thuật (RLS, lộ key) nằm ngoài phạm vi của sản phẩm (xem `data/cases/LABELING.md` mục 2).

| Mã | Số | Nguồn gốc | Đã đọc bản gốc? |
|---|---|---|---|
| B1 | Escape.tech quét **hơn 5.600** app công khai dựng bằng nền tảng vibe coding, thấy **hơn 2.000** lỗ hổng, **hơn 400** secret bị lộ và **175** trường hợp lộ dữ liệu cá nhân (hồ sơ y tế, IBAN, số điện thoại, email). Front-end Lovable chứa JWT ẩn danh nối thẳng tới PostgREST của Supabase. | [Escape.tech — Methodology: How we discovered over 2k high-impact vulnerabilities in apps built with vibe coding platforms](https://escape.tech/blog/methodology-how-we-discovered-vulnerabilities-apps-built-with-vibe-coding/) | ☐ Số lấy qua kết quả tìm kiếm trích trang gốc. Công cụ tải trang bị chặn, **cần mở tay kiểm lại và ghi ngày đăng**. Lưu ý: Escape bán sản phẩm quét bảo mật. |
| B2 | Trong khoảng 20.000 repo công khai có dùng Copilot, **6,4%** lộ ít nhất một secret (trên 1.200 repo). Bản 2026: commit có AI đồng tác giả **dễ lộ secret gấp đôi**. | [GitGuardian — State of Secrets Sprawl 2025](https://www.gitguardian.com/state-of-secrets-sprawl-report-2025) · [2026](https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026/) | ☐ cần mở tay kiểm số |
| B3 | Thử 80 tác vụ viết code trên hơn 100 LLM: **45%** trường hợp code sinh ra có lỗ hổng bảo mật; JavaScript 38–45%. Bản 2026: **44%**. | [Veracode — press release 30/07/2025](https://www.veracode.com/press-release/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/) · [2026 GenAI Report Infographic](https://www.veracode.com/wp-content/uploads/2026-GenAI-Report-Infographic.pdf) | ☐ mới qua thông cáo báo chí; nên trích báo cáo đầy đủ |
| B4 | **Chưa đến 20%** hồ sơ đánh giá tác động chuyển dữ liệu cá nhân xuyên biên giới "đạt chuẩn". *Đây là số duy nhất nói thẳng về nghĩa vụ C1 (Luật 91 Điều 20).* | [VnEconomy](https://vneconomy.vn/chua-den-20-ho-so-danh-gia-tac-dong-chuyen-du-lieu-ca-nhan-xuyen-bien-gioi-dat-chuan.htm) | ☐ **mới đọc tiêu đề**. Cần mở bài để ghi: ai công bố (cơ quan nào), ngày, tổng số hồ sơ. Plan yêu cầu trích nguồn gốc, không trích trang tổng hợp, nên phải tìm văn bản hoặc phát biểu gốc. |

### 2.2 Đào data: corpus 35 repo

35 repo công khai Next.js + Supabase do người Việt dựng (5 chọn tay + 30 tìm tự động), quét tĩnh 27/11/2026 bằng `scanner.case_from_repo` + `agent.answer` chế độ `rule` của Minh, (bộ quét ở commit `f230a48`, trước #6 và #11), rồi **kiểm tay** từng repo bị gắn cờ. Số "không có chỗ lưu đồng ý" chỉ tính trong schema SQL. Chi tiết cách đếm, bảng đầy đủ và 10 ví dụ: `evidence/data-mining.md`. Số máy đếm chỉ để thống kê, không dùng làm nhãn.

| Đếm gì | Kết quả | Cách đếm |
|---|---|---|
| Lưu dữ liệu cá nhân cơ bản (SĐT, email, địa chỉ, họ tên, CCCD…) | **32/35 (91%)** | tên cột trong mọi file `.sql` |
| **Không có chỗ lưu sự đồng ý** (bảng hay cột consent) | **32/35 (91%)** | kiểm chéo tên cột rồi đọc tay từng kết quả; máy đếm 33/35 |
| Có nhật ký đồng ý gần đủ (người dùng + thời điểm + phiên bản) | **2/35** | kiểm tay; máy đếm 1/35 |
| Gọi AI nước ngoài | 11/35 (31%) | máy đếm, chưa kiểm từng lời gọi |
| Gửi dữ liệu cá nhân ra nước ngoài (C1) | **1/35** chắc chắn, +1 chưa rõ (máy đếm 3/35) | kiểm tay |
| Chạm dữ liệu nhạy cảm (ND356 Điều 4) | **2/35** chắc chắn, +1 cần người xem (máy đếm 9/35) | kiểm tay |

**Nghĩa với pain:** gần như mọi app lưu dữ liệu cá nhân, nhưng hầu như không app nào lưu bằng chứng đồng ý → nghĩa vụ C2 (Luật 91 Điều 9) dễ phát sinh mà người dựng không thấy. Ngược lại, C1 và C3-nhạy cảm chỉ chạm một phần nhỏ app → công cụ phải **phân biệt** được, không báo đỏ mọi app (P-c). Bộ quét tự động gắn nhầm 6/9 cờ "nhạy cảm" (chẩn đoán lỗi thiết bị, vị trí xếp hạng SEO, toạ độ quán cafe…) → tên cột thật khó phân loại đúng (P-a).

Ví dụ ban đầu từ 5 repo chọn tay (mã đã ẩn danh):
1. repo-01 (quản lý phòng khám): bảng bệnh nhân có `cccd`, `dob`, `gender`, `phone`, `address`; có bảng `diagnostics`.
2. repo-02 (quản trị nhân sự): `cccd`, `base_salary`, `tax_code`, `personal_income_tax`.
3. repo-03 (quản lý lớp học): `parent_links`, `parent_invitations` gắn học sinh với phụ huynh.
4. repo-04 (bán hàng + VNPay): `phone`, `address` giao hàng.
5. repo-05 (POS bán lẻ + VietQR): khách hàng có `phone`, `address`, công nợ.

### 2.3 Phỏng vấn

Chưa có. **Không điền số trước khi nói chuyện với người thật.**

| | Vai | Gặp pain? | Số lần / 1 tháng qua | Lần gần nhất mất | Đang xoay xở bằng |
|---|---|---|---|---|---|
| P1 | | | | | |
| P2 | | | | | |
| P3 | | | | | |

## 3. ≥5 trích dẫn hoặc ví dụ nguyên văn (có nguồn, bỏ tên)

Ví dụ từ corpus ở mục 2.2 và `evidence/data-mining.md` mục 4 (10 ví dụ, gồm cả báo nhầm). Trích dẫn từ phỏng vấn điền sau.

## 4. Các nguồn có khớp nhau không

Corpus nói: 32/35 app lưu dữ liệu cá nhân, 32/35 không có chỗ lưu sự đồng ý, chỉ 2/35 có nhật ký đồng ý gần đủ, 31% gọi AI nước ngoài. Khớp hướng với số nền B1–B3 (app dựng nhanh xử lý dữ liệu cá nhân thiếu cẩn thận), dù B1–B3 nói về bảo mật chứ không về nghĩa vụ. Lệch: corpus cho thấy C1 (gửi dữ liệu cá nhân ra nước ngoài) **ít hơn** giả thuyết — chỉ 1/35 chắc chắn sau kiểm tay. Phỏng vấn cần trả lời vì sao: không biết, hay biết mà bỏ qua.

## 5. Kết luận

Giả thuyết ở `evidence/hypothesis.md` — *"freelancer/agency dựng app cho SME chưa biết Điều 20 áp cho lời gọi AI"*: **phải đổi một phần**: kết quả corpus gợi ý pain C2 lớn hơn C1, trong khi giả thuyết đặt trước nhấn vào C1. *(Các "cách giải thích khác" ở `hypothesis.md` mục 1b viết sau khi đã thấy số corpus, nên không dùng để nói kết quả này đã được dự đoán.)* Phần "không biết" chưa kiểm được bằng code, chờ phỏng vấn theo ngưỡng đã đặt trước ở `hypothesis.md` mục 2b.
- **Đúng hơn dự kiến ở C2**: thiếu bằng chứng đồng ý là chuyện gần như mọi app (32/35 không có chỗ lưu).
- **Yếu hơn dự kiến ở C1**: 11/35 app gọi AI nước ngoài, nhưng mới chứng minh được 1/35 gửi kèm dữ liệu cá nhân. Chưa biết bộ quét bỏ sót bao nhiêu → cần kiểm ngẫu nhiên các repo không bị gắn cờ.

Điều vẫn chưa biết:
- Bộ quét bỏ sót bao nhiêu ở C1 và dữ liệu nhạy cảm (kiểm ngẫu nhiên 5–10 repo không bị gắn cờ).
- Freelancer có biết Điều 20 áp cho lời gọi AI không, và bao lâu bị khách hỏi một lần (phỏng vấn).

## Lịch hẹn (dùng cho CP2 — chỉ ghi vai và giờ, không tên)

| Vai | Giờ hẹn | Đã xong? |
|---|---|---|
| Freelancer dựng app Next.js + Supabase cho SME | __ | ☐ |
| Agency nhỏ (2–5 người) | __ | ☐ |
| Tech lead startup chuẩn bị gọi vốn | __ | ☐ |
