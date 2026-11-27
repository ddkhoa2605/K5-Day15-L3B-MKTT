# Tổng hợp bằng chứng pain

> Bản đầu cho **CP2 (19:30 Thứ Sáu 27/11)**, bản đủ trước **CP3 10:00 Thứ Bảy 28/11**. Chấm ở rubric R1.
> Người viết: Thắng (G3). Giả thuyết viết trước ở `evidence/hypothesis.md`.
> **Trạng thái CP2:** mới có nghiên cứu bàn giấy + quét thử 5 repo. Chưa nguồn nào đạt ngưỡng (đào data ≥ N đủ lớn, phỏng vấn ≥3, khảo sát ≥20). Corpus 30–50 repo chạy tối Thứ Sáu.

## 0. Bốn pain mà `eval/metric_spec.yaml` trỏ về

Các trường `why` trong `metric_spec.yaml` (đã chốt ở CP2) trỏ về các pain dưới đây. Mỗi pain ghi bằng chứng hiện có và bằng chứng còn thiếu.

| # | Pain (không có chữ AI) | Metric trỏ về | Bằng chứng hiện có | Còn thiếu |
|---|---|---|---|---|
| P-a | **Không biết app đã kích hoạt nghĩa vụ nào**: freelancer đặt tên cột kiểu `tt_sk`, `vi_tri_gan_nhat`, gửi dữ liệu người dùng sang dịch vụ nước ngoài mà không nhận ra đó là chuyển dữ liệu xuyên biên giới | `phan_loai_viet_tat` | Số nền B1, B4 (mục 2.1); quét thử 5/5 repo có cột dữ liệu cá nhân (mục 2.2) | Tỉ lệ X/Y/Z trên corpus 30–50 repo; phỏng vấn xác nhận "không biết" |
| P-b | **Bị khách hoặc nhà đầu tư hỏi mà không trả lời được**: không chỉ ra được căn cứ điều khoản nào, dòng code nào | `trich_dan_dung` | Chưa có số | Phỏng vấn: số lần bị hỏi / tháng, lần gần nhất mất bao lâu |
| P-c | **Tốn thời gian tra cứu cho cả những app không cần**: không biết app nào còn được miễn trừ (ND356 Điều 41) | `bao_dong_gia` | Chưa có số | Phỏng vấn: phút tra cứu / app; corpus: tỉ lệ repo âm tính |
| P-d | **Hậu quả khi không biết nghĩa vụ**: mức phạt tối đa theo ND330 và Luật 91; hồ sơ nộp sai phải làm lại | `tu_choi_dung` | B4 (mục 2.1); mức phạt tối đa theo `data/legal/penalties.json` của Khoa | Nguồn gốc của B4 |

## 1. Nguồn đã dùng

| Nguồn | Đạt ngưỡng? | File |
|---|---|---|
| Đào data: corpus repo công khai Next.js + Supabase (x/N, %, cách đếm chạy lại được, ≥5 ví dụ) | ☐ (mới quét thử n=5, chạy đủ tối Thứ Sáu) | `evidence/data-mining.md` |
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

### 2.2 Đào data: quét thử 5 repo (pilot, chưa phải kết quả)

5 repo công khai Next.js/Supabase do người Việt dựng, **chọn tay** (không ngẫu nhiên) ngày 27/11, đọc 6–8 file `supabase/migrations/*.sql` đầu mỗi repo. Danh sách URL chỉ để trên máy (`data/corpus/index.json`, không commit).

- Có cột dữ liệu cá nhân cơ bản (SĐT, CCCD, địa chỉ, email): **5/5** *(n nhỏ, mẫu chọn tay, không ghi %)*
- Có cột thuộc nhóm nhạy cảm theo ND356 Điều 4 (đọc tay): **1/5** — repo-01 có cột chẩn đoán (tình trạng sức khỏe, ND356 D4.1 điểm d). repo-03 có dữ liệu học sinh và liên kết phụ huynh, cần xác định có thuộc dữ liệu trẻ em hay không.
- Gửi dữ liệu ra API nước ngoài / có nhật ký đồng ý: **chưa đếm**, chờ `case_from_repo()` của Minh.

Ví dụ (mã đã ẩn danh):
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

Bản CP2 mới có 5 ví dụ schema ở mục 2.2. Trích dẫn từ phỏng vấn điền sau.

## 4. Các nguồn có khớp nhau không

Chưa đủ nguồn để so. Số nền B1–B3 nói về bảo mật, B4 nói về hồ sơ C1. Corpus sẽ cho biết freelancer Việt có thật sự gửi dữ liệu ra nước ngoài và thiếu nhật ký đồng ý không. Phỏng vấn sẽ cho biết vì sao.

## 5. Kết luận

Chưa kết luận ở CP2. Điều vẫn chưa biết:
- Tỉ lệ repo gửi dữ liệu cá nhân ra API nước ngoài, thiếu nhật ký đồng ý, chạm dữ liệu nhạy cảm (corpus).
- Freelancer có biết Điều 20 áp cho lời gọi AI không, và bao lâu bị khách hỏi một lần (phỏng vấn).

## Lịch hẹn (dùng cho CP2 — chỉ ghi vai và giờ, không tên)

| Vai | Giờ hẹn | Đã xong? |
|---|---|---|
| Freelancer dựng app Next.js + Supabase cho SME | __ | ☐ |
| Agency nhỏ (2–5 người) | __ | ☐ |
| Tech lead startup chuẩn bị gọi vốn | __ | ☐ |
