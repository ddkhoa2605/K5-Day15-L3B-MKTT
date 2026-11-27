# Đào data — cách đếm và kết quả

> Task G2 (Thắng). Corpus repo công khai Next.js + Supabase của người Việt, phân tích tĩnh.
> Repo chỉ chứa số đã tổng hợp và mã `repo-NN`. **Không ghi tên hay URL repo.** Bản clone và danh sách URL để trên máy (`data/corpus/`, đã gitignore).

## 1. Cách đếm — viết TRƯỚC khi chạy

*(Viết 27/11/2026, trước khi chạy `scripts/scan_corpus.py` trên corpus đầy đủ.)*

- **Data dùng:** repo công khai trên GitHub, tìm qua GitHub Search API ngày 27/11/2026 bằng `scripts/crawl_corpus.py`.
- **Lọc:**
  1. Kết quả của 13 câu tìm kiếm (`supabase nextjs …`, `supabase zalo`, `supabase vnpay`…), sắp theo ngày cập nhật.
  2. Bỏ fork, repo lưu trữ, repo không phải TypeScript/JavaScript, repo > 200 MB.
  3. Có dấu hiệu Việt Nam: mô tả, tên hoặc README chứa chữ có dấu tiếng Việt, hoặc từ `vietnam`, `vnpay`, `momo`, `zalo`, `vietqr`…
  4. Sau khi clone: có Next.js (`next.config.*` hoặc `"next"` trong `package.json`) **và** có schema (`supabase/migrations/*.sql` hoặc file `.sql` có `CREATE TABLE`).
  5. Cộng 5 repo chọn tay lúc 17:00 (repo-01 → repo-05), đánh dấu riêng vì không qua bộ lọc tự động.

  > **Sửa sau lần chạy 1 (27/11 tối):** bước 3 dùng cả chữ `â ê ô` nên lọt 19/40 repo tiếng Bồ Đào Nha, Pháp, Anh (chỉ thấy khi mở code, vd tên hàm tiếng Pháp). Đã đổi bước 3 sang **chỉ chữ riêng của tiếng Việt** (ă đ ơ ư, dấu nặng/hỏi/ngã…, bỏ từ `momo`), và thêm bước 4b: sau khi clone phải có **≥5 file có chữ tiếng Việt**. 19 repo bị loại, còn 21 repo; kết quả lần chạy 1 bỏ, không dùng. Câu tìm kiếm tăng từ 13 lên 20.
- **Đếm gì** (trên mỗi repo, bằng code của Minh ở chế độ `rule`, không gọi model):
  - **X — gửi dữ liệu cá nhân ra nước ngoài:** số repo có C1 = `KICH_HOAT`, tức có lời gọi tới dịch vụ ngoài Việt Nam (AI, email, analytics, HTTP) mà đường đi chạm cột dữ liệu cá nhân. Đếm kèm: số repo có lời gọi ra ngoài bất kỳ, số repo gọi AI.
  - **Y — không có nhật ký đồng ý:** số repo **không** có bảng consent đủ 3 trường (khoá người dùng + thời điểm + phiên bản điều khoản), theo `scanner.find_consent`. Đếm kèm: số repo không có bảng consent nào.
  - **Z — chạm dữ liệu nhạy cảm:** số repo có ít nhất một cột được xếp vào nhóm nhạy cảm theo ND356 Điều 4 (`nhom_nhay_cam` của C3).
- **Mẫu số:** số repo quét được không lỗi (`n_quet_duoc`), không phải số repo tìm thấy. Báo riêng số repo lỗi.
- **Script:** `python scripts/crawl_corpus.py` rồi `python scripts/scan_corpus.py` → `data/corpus/results.csv`, `data/corpus/summary.json`. Người khác chạy lại cùng ngày sẽ ra cùng danh sách (khác ngày thì kết quả tìm kiếm có thể đổi).

## 2. Đọc trước, đếm sau

Đã đọc tay schema của 5 repo đầu (repo-01 → repo-05) trước khi định nghĩa thứ cần đếm. Các *kiểu* thấy được:
- Bảng khách hàng, bệnh nhân, nhân viên có SĐT, CCCD, địa chỉ ở dạng cột thường, đặt tên tiếng Anh hoặc tiếng Việt không dấu.
- Dữ liệu nhạy cảm nằm ở bảng phụ (vd bảng chẩn đoán tách riêng khỏi bảng bệnh nhân).
- Không thấy bảng consent riêng trong 6–8 migration đầu của cả 5 repo (đọc tay, chưa kiểm cả repo).

## 3. Kết quả

*(Điền sau khi chạy `scan_corpus.py`.)*

## 4. ≥5 ví dụ cụ thể (mã đã ẩn danh)

*(Điền sau khi chạy.)*

## 5. Giới hạn của data

- Chỉ repo **công khai** → lệch về dự án học tập, portfolio, đồ án. App thương mại của freelancer thường để private.
- **Phân tích tĩnh**: thấy lời gọi ra ngoài trong code, không biết app có thật sự chạy và gửi dữ liệu thật không. Không gọi endpoint, không chạy app.
- Bộ dò sink và consent dùng quy tắc (regex) → có thể sót lời gọi qua wrapper tự viết, hoặc sót bảng consent đặt tên lạ.
- Lọc "người Việt" bằng chữ có dấu → bỏ sót repo viết README tiếng Anh hoàn toàn.
- Data cho biết người ta **làm gì**, không cho biết **vì sao** (không biết hay biết mà bỏ qua).
  → Kiểm lại bằng phỏng vấn freelancer (`evidence/interviews/`).
