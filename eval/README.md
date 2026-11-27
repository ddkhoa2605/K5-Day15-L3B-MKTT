# Hồ sơ đánh giá — một trang

> Điền ở guide bước 2.4 (mục 1–4, trước CP2) và 4.1 (mục 5–6, trước CP4). Ôn lại: ngày 9, ngày 14 · lab ngày 9. Chấm ở rubric R4, R5.
> Người ngoài nhóm đọc trang này phải hiểu được: nhóm đo cái gì, bằng gì, ra số nào. Trang slide "Đánh giá thế nào" lấy từ đây.

## 1. Dataset → xử lý

Dataset nào, xử lý gì: tóm 2–3 dòng từ `data/DATA_CARD.md`.

## 2. Bộ câu thử dựng ra sao

- `eval/benchmark.csv`: 30 câu (thuong 17 · kho 11 · tu_choi 2, trong đó 2 câu tấn công: `c1-ro-008` chèn lệnh trong schema, `tu-choi-01` xin chứng nhận và tự nộp hồ sơ). Sinh bằng `eval/build_benchmark.py` từ bộ nhãn `data/cases/` (chỉ `split=dev`, không có câu holdout).
- Nguồn (`python run.py check` in sẵn): nguoi_dung 0 · data_that 12 · tu_viet 18 · sinh_seed 0 → từ người dùng / data thật 12/30 (cần ≥1/3). `dt-r01-002` có giả định loại hình và quy mô; không tính câu này thì còn 11/30.
- Độ phủ — lưới 3 chiều: nhóm kiểm (C1/C2/C3) × tag (`ro` rõ ràng · `am` bẫy âm tính · `vt` cột viết tắt · `chatbox` · `luy_ke` · `tan_cong`) × nguồn (data_that / tu_viet):

  | | ro | am | vt | chatbox | luy_ke | tan_cong |
  |---|---|---|---|---|---|---|
  | C1 | 2 thật · 1 tự viết | 2 · 2 | — | 2 · 1 | — | 0 · 1 |
  | C2 | 0 · 1 | 1 · 2 | — | — | — | — |
  | C3 | 3 · 1 | 1 · 1 | 1 · 6 | — | 0 · 1 | — |

  Cộng 1 câu tự do ngoài phạm vi (`tu-choi-01`). Ô trống là ô không có nghĩa (ví dụ chatbox chỉ là bẫy của C1).
- Câu `kho` trỏ về 4 lớp chỗ khó (`spec.md` §5): lớp 1: 0 câu `kho` (lớp này nằm ở câu `thuong` `ro`/`am`) · lớp 2: 0 câu `kho` (thiếu loại hình nằm ở các câu `data_that`, C3 = `CAN_NGUOI_XAC_NHAN`) · lớp 3: 3 câu chatbox (`c1-chat-001`, `dt-r02-004`, `dt-r02-006`) · lớp 4: 8 câu (`vt` ×7, `luy_ke` ×1)

## 3. Metric và cách chấm

| Metric (`eval/metric_spec.yaml`) | Cách chấm | Ngưỡng |
|---|---|---|
| | code / llm / nguoi | |
| | | |
| | | |

- **Người thứ hai chấm thử:** __ (không phải người viết spec) chấm độc lập 5 output → khớp __/5 *(cần ≥4/5; lệch thì viết lại định nghĩa)*
- LLM chấm (nếu có): đã kiểm tay __ câu, khớp __/__
- **Chuẩn "đạt"** (chép nguyên từ `spec.md` §7, chốt trước 19:30 Thứ Sáu 27/11): "__"

## 4. Lệnh

`python run.py eval` → `eval/run-N.csv` + `traces/run-N.jsonl` · điền cột `pass` · `python run.py score eval/run-N.csv`

## 5. Đã chạy gì

| Lượt | Run ID | Model | Cấu hình (prompt / công cụ / thay đổi) | Đạt / tổng | % | Đạt chuẩn? |
|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-005902` | `gpt-6-luna` (chính) · `gpt-6.1-terra` (kiểm chứng) | `SHP_MODE=hybrid` (mặc định) · code `main` `9d8f13f` · benchmark 30 câu | 21/30 | 70% | **Không** — cần ≥ 80% và `trich_dan_dung` 100%; lượt này `trich_dan_dung` 15/21 = 71% |
| 2 | | | | __/__ | | |

Lượt chạy lại vì lỗi kỹ thuật, lượt sau CP4: ghi thêm dòng, không sửa dòng cũ.

## 6. Lỗi chính

Tóm 2–3 dòng từ `eval/report.md`: nhóm lỗi lớn nhất · đã sửa gì · còn lại gì.
