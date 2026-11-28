# Tóm tắt mô phỏng simulate-1@20261128-132012

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| freelancer_agency | 26 | 2 | 2967 | 1637 | 2.7 | 8.0 |
| tech_lead_startup | 12 | 3 | 4300 | 2624 | 3.8 | 12.0 |
| founder_tu_lam | 12 | 1 | 1406 | 761 | 1.2 | 4.0 |

Tỉ lệ đạt dùng để tính: 24/30 (80%) — lượt run-2@20261128-023825

- Tỉ lệ đạt lấy từ lượt nhóm chọn: eval/run-2.csv (--rate-from).

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (200 người) | Chi phí / tháng — cơ sở (1.000 người) | Chi phí / tháng — cao (3.000 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Thực đo — mỗi model giá riêng** (gpt-6-luna + gpt-6.1-terra) | $0.0018 | $0.0022 | $0.0011 | $1.01 | $5.03 | $15.10 | $0.0050 |
| gpt-6-luna (vào 0.1 · ra 0.5 $/1M) — nếu MỌI token tính giá model này | $0.0011 | $0.0014 | $0.00070 | $0.6168 | $3.08 | $9.25 | $0.0031 |
| gpt-6.1-terra (vào 1.0 · ra 5.0 $/1M) — nếu MỌI token tính giá model này | $0.0112 | $0.0140 | $0.0070 | $6.17 | $30.84 | $92.52 | $0.0308 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (2.0) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: gpt-6-luna, gpt-6.1-terra. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/50.
