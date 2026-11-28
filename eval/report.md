# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.
>
> Bản này được viết sau CP4 (tối 28/11), chép số từ các file kết quả đã commit (`eval/run-1.csv` … `run-4.csv`, `python eval/grade.py --dry`, `python run.py score`); không chạy lại, không sửa file kết quả nào. Ghi ở `spec.md` §10.

## 1. Kết quả

Chuẩn "đạt" (`spec.md` §7, chốt trước CP2): **≥ 80% câu qua và `trich_dan_dung` đạt 100%.**

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-005902` | 21/30 | 70% | 12/17 | 7/11 | 2/2 | **chưa đạt** (dưới 80%; `trich_dan_dung` 15/21 = 71%) |
| 2 | `run-2@20261128-023825` | 24/30 | 80% | 12/17 | 10/11 | 2/2 | **chưa đạt** (đủ 80% câu qua, nhưng `trich_dan_dung` 17/21 = 81%) |

Bốn metric (`eval/metric_spec.yaml`, chấm bằng `eval/grade.py`):

| Metric | Ngưỡng | Lượt 1 | Lượt 2 |
|---|---|---|---|
| `phan_loai_viet_tat` | ≥ 85% | 6/7 (n nhỏ, chỉ báo k/n) | 7/7 (n nhỏ) |
| `trich_dan_dung` | 100% | 15/21 = 71% → chưa đạt | 17/21 = 81% → chưa đạt |
| `bao_dong_gia` | ≤ 10% | 1/9 (n nhỏ) | 0/9 (n nhỏ) |
| `tu_choi_dung` | ≥ 90% | 13/14 = 93% → đạt | 14/14 = 100% → đạt |

Hai lượt đo thêm cùng code `b677df6` (sau PR #24, đăng ký trước ở PR #26): `run-3` 24/30 (80%), `run-4` 23/30 (77%), cả hai `trich_dan_dung` 17/21. Model không đặt được temperature nên nhóm báo **khoảng 23–24/30**, không chọn lần đẹp hơn.

Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv` (cột `pass`, `ghi_chu`). Trace: `traces/run-1.jsonl`, `traces/run-2.jsonl`.

## 2. Lỗi lượt 1 — gom thành nhóm có tên

9 câu trượt ở lượt 1. Một câu có thể thuộc hai nhóm.

| Nhóm lỗi | Số câu | Câu |
|---|---|---|
| **A. Bỏ sót dữ liệu cá nhân gửi ra nước ngoài** (C1 ra `KHONG_KICH_HOAT` trong khi nhãn là `KICH_HOAT`): hệ thống không lần ra họ tên, email, ghi âm… đi vào lời gọi API nước ngoài khi dữ liệu đi qua biến trung gian, hàm bọc, hoặc chỉ là địa chỉ người nhận email | 5 | `dt-r02-001`, `dt-r02-002`, `dt-r02-004`, `dt-r02-006`, `dt-r02-008` |
| **B. Gắn nhầm nhóm nhạy cảm `hanh_vi_mang`** (báo động giả): cột mốc thời gian, nội dung chat hoặc toạ độ cố định bị coi là dữ liệu hành vi, kéo theo căn cứ thừa `ND356 D4l` và có câu C3 sai thành `MAT_MIEN_TRU` | 4 | `c1-chat-001`, `c3-vt-003`, `c1-am-003`, `dt-r02-006` |
| **C. Gắn nhầm nhóm `doi_tu_rieng_tu`** cho bảng quan hệ phụ huynh, bảng ghi âm cuộc gọi | 2 | `dt-r02-001`, `dt-r03-002` |
| **D. Không nhận ra trường hợp cần luật sư** (chatbox gửi nguyên văn chữ người dùng tự gõ) | 1 | `c1-chat-001` |

**≥3 lỗi cụ thể:**

| Câu | Input (tóm tắt) | Output | Vì sao sai |
|---|---|---|---|
| `dt-r02-004` (nhóm A) | Phần mềm nội bộ: component gửi `{ query, role, name: user.full_name }`, route server đưa họ tên vào system prompt rồi gọi Claude (Anthropic) | C1 = `KHONG_KICH_HOAT`, thiếu `Luat91 D20.1`, `D20.2` | Họ tên nhân viên đi qua body request rồi vào prompt gửi ra nước ngoài; bộ kiểm chứng không lần được qua biến `name` nên kết luận "không gửi". Đây là lỗi người dùng tin "sạch" rồi bỏ sót nghĩa vụ |
| `dt-r02-001` (nhóm A, C) | Cron job gửi nguyên file ghi âm cuộc gọi với khách sang Gemini để chép lời, rồi gửi bản chép sang Claude để chấm | C1 = `KHONG_KICH_HOAT`, C2 = `KHONG_KICH_HOAT`, thừa nhóm `doi_tu_rieng_tu`, thiếu 4 mã căn cứ | Dữ liệu cá nhân nằm trong âm thanh (`inline_data`), không phải tên cột, nên hệ thống không thấy; đồng thời gắn nhầm nhóm nhạy cảm cho bảng cuộc gọi |
| `c1-am-003` (nhóm B) | App đặt sân pickleball hiển thị bản đồ Google Maps theo toạ độ **cố định của sân** do chủ sân nhập, không lấy vị trí người dùng | C3 = `MAT_MIEN_TRU`, thừa nhóm `hanh_vi_mang`, thừa `ND356 D4l` | Cột `vi_tri_san_lat/lng` là vị trí của sân, không phải của người; model phân loại theo từ "vị trí" nên app mất miễn trừ oan (báo động giả) |
| `c1-chat-001` (nhóm B, D) | Khung chat gửi nguyên văn chữ người dùng tự gõ sang OpenAI, không gắn email, tên hay id | C1 = `KHONG_KICH_HOAT` (nhãn `CAN_LUAT_SU`), C3 = `MAT_MIEN_TRU`, thừa `hanh_vi_mang` | Chữ tự do có thể chứa dữ liệu cá nhân mà code không biết trước, nên nhãn yêu cầu chuyển luật sư; hệ thống vừa kết luận chắc chắn "không kích hoạt", vừa coi cột `noi_dung` là nhạy cảm |

## 3. Một lần cải tiến

- **Nhắm vào nhóm lỗi:** A (bỏ sót dữ liệu gửi ra nước ngoài), kèm B. **Vì sao A đau nhất với người dùng:** freelancer tin kết luận "không kích hoạt" rồi bàn giao app, bỏ sót nghĩa vụ chuyển dữ liệu xuyên biên giới (Luật 91 Điều 20); đây là tác hại số (1) ở `spec.md` §9. B gây báo động giả (khách lo thừa, tốn tiền hồ sơ), nhẹ hơn.
- **Đã sửa gì** (PR #15 của Minh, `main` `e33792d`, ghi ở `spec.md` §10):
  - Kiểm chứng C1 lần theo dữ liệu tới lời gọi ra ngoài: khối đối số, biến trung gian, lát cắt ngược, hàm bọc (nhóm A).
  - Quy tắc người nhận email: gửi email tới người dùng qua dịch vụ đặt ngoài Việt Nam thì C1 = `KICH_HOAT` (Khoa chốt sau lượt 1, nhóm A).
  - Prompt phân loại: cột mốc thời gian, `*_at`, định danh kỹ thuật không phải `hanh_vi_mang`; ngoại lệ bảng hành vi (nhóm B).
  - Cột chữ tự do của người dùng không tự nó nhạy cảm, kèm lời nhắc (nhóm B, D).
- **Kết quả:** nhóm A 0/5 → 1/5 đạt (chỉ `dt-r02-006`); nhóm B 0/4 → 4/4 đạt; nhóm C 0/2 → 1/2 (`dt-r02-001` hết lỗi nhóm nhưng vẫn trượt vì C1, C2); nhóm D 0/1 → 1/1. **Tổng 70% → 80%** (21 → 24/30). `trich_dan_dung` 71% → 81%.
- **Nói thẳng:** cải tiến đo được nằm chủ yếu ở nhóm B, không phải nhóm A mà nhóm nhắm tới. 4/5 câu nhóm A vẫn trượt ở lượt 2, nên lỗi nguy hiểm nhất **chưa được sửa**.
- **Câu nào tệ đi sau khi sửa:** `dt-r01-001` (đạt → trượt: thừa nhóm `dinh_danh_dien_tu`). `dt-r02-002` vẫn trượt nhưng đổi kiểu: C1 từ `KHONG_KICH_HOAT` sang `CAN_LUAT_SU`.
- **Lượt 2 có phần lạc quan:** các thay đổi làm sau khi xem lỗi lượt 1, và Minh đã đo nháp trên benchmark lúc sửa. Cải thiện nằm hết ở câu tự viết (15/18 → 18/18); câu từ code thật (`data_that`) giữ nguyên 6/12, và cả 6 câu còn trượt ở lượt 2 đều là câu code thật.

## 4. Còn lại

- **Lỗi chưa sửa và nguy hiểm thế nào:**
  - Nhóm A trên code thật (`dt-r02-001`, `-002`, `-004`, `-008`): hệ thống nói "không kích hoạt" C1 trong khi app gửi họ tên nhân viên, ghi âm cuộc gọi sang Anthropic, Google. Người dùng tin kết luận này thì bỏ sót nghĩa vụ hồ sơ chuyển dữ liệu xuyên biên giới. Sản phẩm giảm rủi ro này bằng cách luôn nói "không thấy bằng chứng trong mã nguồn đã quét" thay vì "an toàn", và hiện danh sách lời gọi ra ngoài để người xem lại, nhưng lỗi vẫn còn.
  - `trich_dan_dung` 81%, chưa tới 100%: mọi mã đều có trong `citations.json` (không bịa mã), nhưng tập mã thiếu `Luat91 D20.1`, `D20.2` vì C1 sai ở trên.
  - Gắn nhầm nhóm nhạy cảm còn 2 câu (`dt-r01-001`, `dt-r03-002`).
  - Bộ mù 12 câu (`eval/blind.manifest`, cách đọc kết quả viết trước ở `eval/blind_doc_ket_qua.md`) **chưa chạy**; holdout cũ 10 câu: hybrid 8/10, rule 8/10, chỉ LLM 0/10 (PR #19). Nhãn do nhóm tự dán, chưa qua luật sư.
- **Nếu có thêm 1 tuần:** (1) theo dữ liệu qua nhiều file và qua tệp nhị phân (âm thanh, ảnh) cho C1, đo trên phần code thật trước, không chỉnh theo benchmark; (2) chạy bộ mù đúng một lần sau `code-freeze`, báo theo quy tắc đã viết trước; (3) nhờ một luật sư xem lại các giả định C1 (email, hạ tầng nền) và C3 (cột chữ tự do); (4) phỏng vấn 3 freelancer để có số impact cho `spec.md` §2.
