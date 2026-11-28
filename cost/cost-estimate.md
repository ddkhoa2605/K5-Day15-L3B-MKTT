# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate` → chép bảng trong `cost/simulate-N-summary.md` vào đây.
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`): 3 kiểu — `freelancer_agency` (50%, 4 phiên / người / tháng, 2 lượt hỏi / phiên) · `tech_lead_startup` (20%, 2 phiên, 3 lượt) · `founder_tu_lam` (30%, 1 phiên, 1 lượt). Nguồn: *(tự ước tính)* — chưa có phỏng vấn để thay.
- **Số người dùng thật** 3 kịch bản: thấp 200 · cơ sở 1.000 · cao 3.000. Nguồn: *(tự ước tính)* — chưa có số công khai về số freelancer/agency dựng app Next.js + Supabase cho SME ở Việt Nam.
- **Giá** 2 mức model: `gpt-6-luna` vào $0.10 · ra $0.50 / 1M token · `gpt-6.1-terra` vào $1.00 · ra $5.00 / 1M token. Nguồn: https://developers.openai.com/api/docs/pricing, bảng Standard, short context, xem 27/11/2026 (chưa đối chiếu `further-reading/model-prices.md` của repo đề).
- **Tỉ lệ đạt** dùng để tính: 24/30 (80%) — lượt `run-2` (run-2@20261128-023825, lượt 2), qua `--rate-from eval/run-2.csv`.
- Đo token trên model `gpt-6-luna` (phân loại cột) và `gpt-6.1-terra` (kiểm chứng đường đi), tính giá model `gpt-6-luna` và `gpt-6.1-terra` (dòng "thực đo" tính mỗi model theo giá riêng).

## 2. Kết quả mô phỏng

Lượt mô phỏng: `cost/simulate-1.csv` · run ID simulate-1@20261128-132012 · 50 phiên (0 phiên lỗi) · seed 42

Lệnh: `python run.py simulate --rate-from eval/run-2.csv`. Bảng chép từ `cost/simulate-1-summary.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| freelancer_agency | 26 | 2 | 2967 | 1637 | 2.7 | 8.0 |
| tech_lead_startup | 12 | 3 | 4300 | 2624 | 3.8 | 12.0 |
| founder_tu_lam | 12 | 1 | 1406 | 761 | 1.2 | 4.0 |

| Model | Chi phí / phiên | Chi phí / task thành công | / tháng — thấp (200) | / tháng — cơ sở (1.000) | / tháng — cao (3.000) | / người / tháng (cơ sở) |
|---|---|---|---|---|---|---|
| **Thực đo — mỗi model giá riêng** (gpt-6-luna + gpt-6.1-terra) | $0.0018 | **$0.0022** | $1.01 | $5.03 | $15.10 | $0.0050 |
| gpt-6-luna — nếu MỌI token tính giá model này | $0.0011 | $0.0014 | $0.6168 | $3.08 | $9.25 | $0.0031 |
| gpt-6.1-terra — nếu MỌI token tính giá model này | $0.0112 | $0.0140 | $6.17 | $30.84 | $92.52 | $0.0308 |

Chi phí / task thành công = chi phí trung bình mỗi phiên ÷ tỉ lệ đạt — **không coi như đạt 100%**.

Ghi chú: token đo trên code hiện tại (sau commit b677df6, phương án (b)); tỉ lệ đạt lấy từ run-2 như đề yêu cầu. changelog ở `spec.md` §10 ghi token vào của phương án (b) ngang mốc trước đó (~70k so với ~69k / 50 câu).

## 3. So với impact

- Impact / người / tháng (`spec.md` §2): *(chưa đo)* — §2 chưa có số người gặp, số lần / tháng và thời gian mỗi lần.
- Chi phí / người / tháng (cơ sở, model gpt-6-luna + gpt-6.1-terra): $0.0050 (≈ $5.03 / tháng cho 1.000 người).
- **Kết luận một dòng — đáng làm không:** chi phí model không phải rào cản (dưới 1 cent / người / tháng kể cả khi tính toàn bộ token theo giá gpt-6.1-terra); còn đáng làm hay không phụ thuộc impact, mà impact chưa đo nên chưa kết luận được.

## 4. *(Muốn sâu hơn, không bắt buộc)*

- Bảng độ nhạy: model rẻ hơn · cache · cắt ngữ cảnh · giới hạn bước — mỗi cần gạt đổi chi phí bao nhiêu
- Chi phí ngoài model: hosting, lưu trữ, giờ công người duyệt
- Quy mô nào thì bài toán còn đáng làm
