# Ablation — tập `holdout` · n=10

Chạy 28/11/2026 02:44 · commit `81e8ef3` · lệnh `python eval/ablation.py --tap holdout` · MODEL_PROVIDER=`openai`

Model thực tế: A · rule: không gọi model · B · llm: gpt-6-luna · C · hybrid: gpt-6-luna, gpt-6.1-terra

## 1. Bốn metric (eval/metric_spec.yaml)

Mỗi ô: k/n = % [khoảng tin cậy Wilson 95%]. n nhỏ nên khoảng rộng; hai chế độ chỉ khác nhau thật khi khoảng ít chồng nhau.

| Metric | Ngưỡng | A · rule | B · llm | C · hybrid |
|---|---|---|---|---|
| `phan_loai_viet_tat` | >= 85% | 1/2 = 50% [9–91] · n nhỏ | 2/2 = 100% [34–100] · n nhỏ | 2/2 = 100% [34–100] · n nhỏ |
| `trich_dan_dung` | >= 100% | 5/7 = 71% [36–92] · n nhỏ | 0/7 = 0% [0–35] · n nhỏ | 6/7 = 86% [49–97] · n nhỏ |
| `bao_dong_gia` | <= 10% | 0/3 = 0% [0–56] · n nhỏ | 3/3 = 100% [44–100] · n nhỏ | 1/3 = 33% [6–79] · n nhỏ |
| `tu_choi_dung` | >= 90% | 0/1 = 0% [0–79] · n nhỏ | 0/1 = 0% [0–79] · n nhỏ | 1/1 = 100% [21–100] · n nhỏ |
| **% câu đạt (pass)** | — | 8/10 = 80% [49–94] | 0/10 = 0% [0–28] | 8/10 = 80% [49–94] |

`n nhỏ` = mẫu dưới 10 câu: chỉ đọc k/n, không kết luận theo %.

## 2. % câu đạt theo tag

| tag | A · rule | B · llm | C · hybrid |
|---|---|---|---|
| `ro` | 3/3 = 100% · n nhỏ | 0/3 = 0% · n nhỏ | 2/3 = 67% · n nhỏ |
| `vt` | 1/2 = 50% · n nhỏ | 0/2 = 0% · n nhỏ | 2/2 = 100% · n nhỏ |
| `am` | 3/3 = 100% · n nhỏ | 0/3 = 0% · n nhỏ | 2/3 = 67% · n nhỏ |
| `chatbox` | 0/1 = 0% · n nhỏ | 0/1 = 0% · n nhỏ | 1/1 = 100% · n nhỏ |
| `luy_ke` | 1/1 = 100% · n nhỏ | 0/1 = 0% · n nhỏ | 1/1 = 100% · n nhỏ |

## 3. Chi phí mỗi case (trung bình)

| | A · rule | B · llm | C · hybrid |
|---|---|---|---|
| token vào | 0.0 | 3903.9 | 1399.3 |
| token ra | 0.0 | 854.2 | 753.3 |
| số lần gọi model | 0.0 | 1.0 | 1.3 |
| thời gian (giây) | 0.0 | 6.4 | 5.9 |
| case lỗi | 0 | 0 | 0 |

## 4. Nhận xét tự động
- `phan_loai_viet_tat` (tag vt): C − A = **+50 điểm %** (A 1/2 = 50% [9–91] · n nhỏ, C 2/2 = 100% [34–100] · n nhỏ); hai khoảng tin cậy chồng nhau nên chưa đủ để khẳng định khác biệt.
- Chi tiết từng case: `eval/ablation-holdout-<mode>.csv`.
