# Hồ sơ đánh giá — một trang

> Điền ở guide bước 2.4 (mục 1–4, trước CP2) và 4.1 (mục 5–6, trước CP4). Ôn lại: ngày 9, ngày 14 · lab ngày 9. Chấm ở rubric R4, R5.
> Người ngoài nhóm đọc trang này phải hiểu được: nhóm đo cái gì, bằng gì, ra số nào. Trang slide "Đánh giá thế nào" lấy từ đây.

## 1. Dataset → xử lý

Ba nguồn (chi tiết `data/DATA_CARD.md`): (1) văn bản luật công khai (Luật 91/2025/QH15, Nghị định 356/2025, bản tin EY về Nghị định 330) tách thành 391 chunk, từ đó Khoa dựng bảng luật `data/legal/*.json` đối chiếu tay; (2) 60 case tự viết có nhãn C1/C2/C3 (`data/cases/cases.jsonl`, nhãn commit trước commit đầu của `codebase/rules.py`); (3) case trích từ code thật của repo công khai Next.js + Supabase, đã ẩn danh (`data/cases/corpus_cases.jsonl`). Không có dữ liệu cá nhân thật.

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
| `phan_loai_viet_tat`: câu tag `vt`, tập nhóm nhạy cảm trong output trùng đúng nhãn | code (`eval/grade.py`) | ≥ 85% |
| `trich_dan_dung`: mọi mã điều khoản có trong `data/legal/citations.json` và tập mã bằng đúng nhãn | code | 100% |
| `bao_dong_gia`: câu tag `am`, tỉ lệ có nhóm bị báo kích hoạt sai | code | ≤ 10% |
| `tu_choi_dung`: câu nhãn cần luật sư / cần người xác nhận, chatbox, tấn công: từ chối đúng, không kết luận chắc chắn | code | ≥ 90% |

Metric có n < 10 chỉ báo k/n, không kết luận theo % (`SMALL_N` trong `grade.py`).

- **Người thứ hai chấm thử:** Nguyễn Văn Minh (không phải người viết spec) chấm độc lập 5 output → khớp 5/5 *(cần ≥4/5; lệch thì viết lại định nghĩa)*
  - Lấy mẫu đều trong `eval/run-2.csv` (dòng 1, 7, 13, 19, 25, mỗi dòng cách nhau 6 câu, không chọn tay). Chấm theo `pass_criterion`: đọc khối JSON cuối output, so trạng thái C1/C2/C3, tập `C3.nhom_nhay_cam`, tập `can_cu`, và kiểm mọi mã có trong `data/legal/citations.json`. Chấm xong mới so với cột `pass`.

    | Câu | Loại | Người hai chấm | Cột `pass` | Lý do |
    |---|---|---|---|---|
    | `c1-ro-001` | thuong | 1 | 1 | 3 trạng thái, nhóm (rỗng), căn cứ đều khớp |
    | `c1-chat-001` | kho | 1 | 1 | C1 `CAN_LUAT_SU` + `Luat91 D20.6` khớp |
    | `dt-r01-001` | thuong | 0 | 0 | Thừa nhóm `dinh_danh_dien_tu` (expected chỉ `suc_khoe`) |
    | `dt-r03-002` | thuong | 0 | 0 | Thừa nhóm `doi_tu_rieng_tu` (expected rỗng) |
    | `c3-vt-004` | kho | 1 | 1 | Đủ 5 căn cứ, nhóm `tai_chinh` khớp |

  - Giới hạn: tiêu chí là so khớp chính xác nên hai người chấm gần như chắc chắn khớp nhau. Chỗ có thể lệch là `dt-r01-001`: hệ thống gắn `dinh_danh_dien_tu` vì có cột `cccd`, việc này có thể hợp lý về mặt pháp lý nhưng vẫn trượt vì nhãn chỉ ghi `suc_khoe`. Mình không sửa `expected`; nếu muốn, câu này nên ghi vào cờ cần Khoa xem lại trong `LABELING.md`.
- LLM chấm: không dùng; cả 4 metric chấm bằng code.
- **Chuẩn "đạt"** (chép nguyên từ `spec.md` §7, chốt trước 19:30 Thứ Sáu 27/11): "Đạt khi ≥ 80% câu trong `eval/benchmark.csv` qua (cột `pass` = 1), và `trich_dan_dung` đạt 100%."

## 4. Lệnh

`python run.py eval` → `eval/run-N.csv` + `traces/run-N.jsonl` · điền cột `pass` · `python run.py score eval/run-N.csv`

## 5. Đã chạy gì

| Lượt | Run ID | Model | Cấu hình (prompt / công cụ / thay đổi) | Đạt / tổng | % | Đạt chuẩn? |
|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-005902` | `gpt-6-luna` (chính) · `gpt-6.1-terra` (kiểm chứng) | `SHP_MODE=hybrid` (mặc định) · code `main` `9d8f13f` · benchmark 30 câu | 21/30 | 70% | **Không** — cần ≥ 80% và `trich_dan_dung` 100%; lượt này `trich_dan_dung` 15/21 = 71% |
| 2 | `run-2@20261128-023825` | `gpt-6-luna` (chính) · `gpt-6.1-terra` (kiểm chứng) | `SHP_MODE=hybrid` · code `main` `e33792d` (sau PR #15): prompt phân loại (cột mốc thời gian, `*_at`, định danh kỹ thuật, ngoại lệ bảng hành vi); C1 lần theo dữ liệu (khối đối số, lát cắt ngược, hàm bọc); kiểm chứng phân biệt chữ người dùng cuối với nội dung nghiệp vụ; quy tắc người nhận email và cột chữ tự do (Khoa chốt sau lượt 1, `spec.md` §7, §10) · benchmark giống hệt lượt 1 | 24/30 | 80% | **Không**: đạt ngưỡng 80% câu qua, nhưng `trich_dan_dung` 17/21 = 81% (cần 100%) |
| 3 | `run-3@20261128-063957` | `gpt-6-luna` (chính) · `gpt-6.1-terra` (kiểm chứng) | `SHP_MODE=hybrid` · code `main` `b677df6` (sau #24, xem `spec.md` §10) · benchmark giống hệt lượt 1 · **lần đo 1/2 cùng code** (đăng ký trước ở PR #26) | 24/30 | 80% | **Chưa đạt chuẩn**: `trich_dan_dung` 17/21 = 81% (cần 100%) |
| 4 | `run-4@20261128-064333` | `gpt-6-luna` (chính) · `gpt-6.1-terra` (kiểm chứng) | `SHP_MODE=hybrid` · code `main` `b677df6` (sau #24, xem `spec.md` §10) · benchmark giống hệt lượt 1 · **lần đo 2/2 cùng code** (đăng ký trước ở PR #26) | 23/30 | 77% | **Chưa đạt chuẩn**: dưới 80% câu qua; `trich_dan_dung` 17/21 = 81% (cần 100%) |

Lượt chạy lại vì lỗi kỹ thuật, lượt sau CP4: ghi thêm dòng, không sửa dòng cũ.

**Xác nhận code lúc chạy** (trace của khung không ghi commit):
- **Lượt 1:** chạy trên nhánh `T2-run-1` vừa tách từ `main` `9d8f13f`, chưa sửa file code nào. Kiểm lại: `git log -1 --format=%p 0127469` ra `9d8f13f` (cha của commit kết quả), và `git show --stat 0127469` chỉ có `eval/run-1.csv`, `traces/run-1.jsonl`, `eval/README.md`.
- **Lượt 2:** chạy trên nhánh `T2-run-2` vừa tách từ `main` `e33792d`. Trước khi chạy đã ghi `git rev-parse --short HEAD` = `e33792d`; `git status --short` không có file code nào bị sửa; `eval/benchmark.csv` và `eval/metric_spec.yaml` giống hệt lúc lượt 1 (`git diff --quiet 0127469 HEAD -- …`).
- **Lượt 2 có phần lạc quan:** các thay đổi của PR #15 được làm **sau khi xem lỗi lượt 1**, và Minh đã đo nháp trên benchmark trong lúc sửa (không ghi vào `eval/`, `traces/`). Vì vậy số lượt 2 không phải số kiểm tra độc lập; holdout mới là số đó. Cải thiện nằm hết ở câu tự viết (15/18 → 18/18); câu `data_that` giữ nguyên 6/12 (`dt-r02-006` trượt → đạt, `dt-r01-001` đạt → trượt), và cả 6 câu còn trượt đều là câu `data_that`.
- **Lượt 3 và 4:** hai lần đo **cùng code** `b677df6` trên nhánh `T2-run-3-4`, đăng ký trước ở PR #26 (mở trước khi chạy). Trước mỗi lần chạy, `git status --short` không có file code nào bị sửa; benchmark và `metric_spec.yaml` giống hệt lượt 1. Model không đặt được temperature nên báo **khoảng 23–24/30**, không chọn lần đẹp hơn. Đồng hồ máy chạy chậm khoảng 77 giây so với GitHub, nên giờ trong run ID sớm hơn giờ GitHub ghi cho PR.
- **Lượt sau làm giống:** ngay trước `python run.py eval`, ghi `git rev-parse --short HEAD`, và `git status --short` không có file code nào bị sửa. Chạy xong commit kết quả ngay, không kèm thay đổi code.

## 6. Lỗi chính

Chi tiết `eval/report.md`. Nhóm lỗi nguy hiểm nhất là **bỏ sót dữ liệu cá nhân gửi ra nước ngoài** (C1 âm tính giả, 5/9 câu trượt ở lượt 1, đều từ code thật). PR #15 thêm lần theo dữ liệu qua biến trung gian, hàm bọc và quy tắc người nhận email, đồng thời sửa prompt phân loại cột mốc thời gian, cột chữ tự do: lượt 1 → lượt 2 là 70% → 80%, nhưng phần tăng nằm chủ yếu ở nhóm gắn nhầm `hanh_vi_mang` (4/4 hết lỗi); nhóm bỏ sót C1 chỉ sửa được 1/5. Còn lại: 4 câu C1 trên code thật, `trich_dan_dung` 81% (chưa tới 100%) nên **chưa đạt chuẩn** ở cả bốn lượt; bộ mù 12 câu chưa chạy.
