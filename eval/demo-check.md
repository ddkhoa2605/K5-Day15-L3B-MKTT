# Kiểm 3 repo demo (T3, bước 2)

Chạy lúc 27/11/2026 22:50, trên code `main` = `f102f82` (đã có PR #6 và #8). Model: `gpt-6-luna` dùng để phân loại cột, `gpt-6.1-terra` dùng để kiểm chứng đường đi, `MODEL_MAX_TOKENS=4000`. Kịch bản cài sẵn của từng repo xem ở `data/demo_repos/README.md`.

Cách chạy (cũng là thứ hiện ra khi demo):

```
python run.py            # rồi dán:  repo:data/demo_repos/repo_a   (b, c tương tự)
```

Để chốt C3 cho repo C: lấy case từ `scanner.case_from_repo("data/demo_repos/repo_c")`, thêm
`"loai_hinh": "doanh_nghiep_sieu_nho", "so_chu_the_luy_ke": 4200`, rồi dán dòng JSON đó vào `python run.py`.

## Kết quả

Chạy mỗi repo **một lần** ở mỗi chế độ. Chế độ `rule` không gọi model. Chế độ `hybrid` là chế độ mặc định khi demo.

| Repo | Kỳ vọng | `rule` | `hybrid` (model thật) | Token hybrid (vào / ra) |
|---|---|---|---|---|
| A · tiệm bánh | C1 KHONG · C2 KHONG | ✅ C1 KHONG · C2 KHONG · C3 CAN_NGUOI_XAC_NHAN | ✅ giống rule | 1260 / 665 |
| B · chat AI | C1 KICH_HOAT, bằng chứng `app/api/chat/route.ts:13` · C2 KHONG | ✅ C1 KICH_HOAT (`Luat91 D20.1`, `D20.2`) tại `route.ts:13` · C2 KHONG · C3 CAN_NGUOI_XAC_NHAN, nhom `[]` | ⚠️ C1, C2 đúng như rule; **C3 nhom `[hanh_vi_mang]`** (sai, xem lỗi 1) | 1303 / 873 |
| C · đặt sân, bước 1 (`repo:`) | C2 KICH_HOAT_NANG · C3 có `vi_tri_dinh_vi` | ✅ C2 KICH_HOAT_NANG (`Luat91 D9.3`, `ND356 D6`, `ND356 D6.3`) tại `components/DangKyForm.tsx:10` · C3 CAN_NGUOI_XAC_NHAN, nhom `[vi_tri_dinh_vi]` tại `001_init.sql:19` | ✅ giống rule | 873 / 784 |
| C · bước 2 (JSON khai siêu nhỏ, 4.200) | C3 MAT_MIEN_TRU (`ND356 D4h`, `Luat91 D38.3`, `ND356 D41.2`) | ✅ đúng kỳ vọng | ⚠️ C3 MAT_MIEN_TRU nhưng **thừa nhóm `hanh_vi_mang` và mã `ND356 D4l`** (lỗi 1); bằng chứng C3 ra `None:None` (lỗi 2) | 884 / 955 |

**Kết luận chính khớp kỳ vọng ở cả 3 repo, cả 2 chế độ.** C1 của B, C2 của C, và việc repo C mất miễn trừ sau khi khai loại hình đều ra đúng. Danh sách "đã gửi ra ngoài" (`da_gui_ra_ngoai`) chỉ có tên cột và đoạn code `file:dòng (đã lọc secret)`, không có dữ liệu.

## Lỗi cần sửa trước buổi demo (báo Minh)

1. **`hybrid` phân loại cột thời gian thành `hanh_vi_mang`.** Model gắn `chat_messages.created_at` (repo B), `bookings.gio_bat_dau` và `bookings.created_at` (repo C, bước 2) vào nhóm "dữ liệu theo dõi hành vi" (ND356 Điều 4 điểm l). Mốc thời gian của một lượt đặt sân hay một tin nhắn không phải theo dõi hành vi. Lỗi này **không ổn định**: cùng repo C, bước 1 không bị nhưng bước 2 bị. Trên sân khấu, bước 2 sẽ trích thêm `ND356 D4l` cho cột "giờ bắt đầu".
   - Đề xuất: thêm vào prompt phân loại một câu kiểu "cột mốc thời gian (`*_at`, `gio_*`, `ngay_*`) không phải dữ liệu theo dõi hành vi trừ khi bảng ghi log thao tác người dùng".
   - Đề xuất cho demo: cache sẵn kết quả (plan, khung 12:00–14:30).
   - Repo demo **không** nằm trong benchmark hay bộ nhãn, nên sửa prompt theo lỗi này không làm hỏng số đo.
2. **Bước 2 (dán JSON) mất `file:dòng` của bằng chứng C3.** `case_from_repo` trả `schema` dạng chuỗi `bang(cot, …)` nên mất vị trí từng cột. Khi gửi lại case dạng JSON, bằng chứng C3 ra `None:None`. Ở bước 1 (`repo:`) thì có đủ (`001_init.sql:19`).
3. **Đầu vào `repo:` chưa nhận được loại hình doanh nghiệp.** Vì vậy demo repo C phải đi 2 bước (`repo:`, rồi dán JSON). Nếu `answer()` nhận thêm `repo:<path> loai_hinh=… so_chu_the=…`, demo sẽ gọn hơn.

## Ghi chú

- Trong lần chạy đầu tiên, repo demo có comment mô tả tình huống ở đầu file SQL. Scanner đã đọc comment đó như code thật (bằng chứng C2 trỏ vào dòng comment). Mình đã bỏ toàn bộ comment trong code; phần mô tả chuyển sang `data/demo_repos/README.md`. Bảng trên là kết quả sau khi sửa.
- Mỗi chế độ mới chạy 1 lần, nên chưa đo độ ổn định của `hybrid`. Nên chạy demo vài lần trước buổi trình bày (plan K4: tập 5 lần).
