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
  >
  > **Bổ sung để đủ mẫu (27/11 đêm, đã đăng nhập GitHub):** thêm 17 câu tìm theo ngành SME (tiếng Việt không dấu) và 8 câu **tìm trong code** chuỗi giao diện tiếng Việt (`"Đăng nhập"`, `"Số điện thoại"`, `"Họ và tên"`…) trong repo dùng Supabase. Trước khi clone hỏi cây thư mục qua API, bỏ repo không có Next.js hoặc không có file `.sql`. Bộ lọc sau clone giữ nguyên. Kết quả: **35 repo** (5 chọn tay + 30 tự động). Mã `repo-NN` không liên tục vì repo bị loại không dùng lại số.
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

Quét 27/11/2026, **N = 35 repo**, quét được 35/35 (0 lỗi). Số "máy đếm" là output chế độ `rule`; số "kiểm tay" là sau khi người đọc bằng chứng (dòng code / tên cột) của từng repo bị gắn cờ. **Số máy đếm chỉ để thống kê, không dùng làm nhãn.**

> **Phiên bản bộ quét đã dùng:** `codebase/scanner.py` ở commit `f230a48` (file đổi lần cuối ở `2609dcf`), chạy trên nhánh `thang/g2-corpus` tối 27/11 — tức **trước** thay đổi scanner của `bbe1055` (vào `main` qua #6) và **trước PR #11**. Chạy lại bằng bộ quét mới hơn sẽ ra số máy đếm khác (vd hết báo nhầm Mailchimp ở C1, Y nhận ra repo-02 vì email/SĐT được tính là khoá người dùng). Muốn tái lập đúng bảng dưới: `git checkout f230a48 -- codebase/` rồi chạy `scripts/scan_corpus.py`. Cột "kiểm tay" không phụ thuộc phiên bản bộ quét.

| Đếm gì | Máy đếm | Kiểm tay | Ghi chú |
|---|---|---|---|
| Có lời gọi ra dịch vụ ngoài (AI, email, analytics, HTTP) | 17/35 (49%) | — | Chưa kiểm tay từng lời gọi |
| … trong đó gọi AI nước ngoài | 11/35 (31%) | — | |
| **X** — gửi dữ liệu cá nhân ra nước ngoài (C1 = `KICH_HOAT`) | 3/35 (9%) | **1/35** chắc chắn, +1 chưa rõ | 1 repo là chuỗi chữ trong script tạo tài liệu (báo nhầm); 1 repo gửi qua SMTP, không biết máy chủ đặt ở đâu |
| **Y** — không có nhật ký đồng ý đủ 3 trường (người dùng + thời điểm + phiên bản) | 34/35 (97%) | **33/35 (94%)** | Kiểm tay: 2 repo có nhật ký gần đủ — repo-17 (bảng `consents`) và repo-02 (bảng `dong_y_du_lieu` có email/SĐT, thời điểm, phiên bản; máy chấm thiếu vì định danh bằng email/SĐT thay vì `user_id`) |
| … không có chỗ nào lưu sự đồng ý (bảng hay cột) | 33/35 (94%) | **32/35 (91%)** | Kiểm chéo bằng tìm tên cột (`consent*`, `agreed_at`, `accepted_at`, `policy_version`…) trong mọi file `.sql` rồi đọc từng kết quả: 6 repo khớp, nhưng 3 là trùng tên (thời điểm dịch vụ email nhận thư, thời điểm chốt kết quả giải đấu, phiên bản quy trình khám). Chỉ 3 repo thật sự có: repo-02, repo-17, repo-44 (`leads.consent_marketing` — chỉ cờ đúng/sai, không có thời điểm, phiên bản) |
| **Z** — chạm dữ liệu nhạy cảm (ND356 Điều 4) | 9/35 (26%) | **2/35 (6%)** chắc chắn, +1 cần người xem | 6/9 là báo nhầm (xem mục 4) |

**Đọc số này thế nào:**
- **Y là số mạnh nhất**: 32/35 repo không có chỗ nào trong schema để lưu sự đồng ý của người dùng, dù 32/35 repo có cột dữ liệu cá nhân cơ bản (SĐT, email, địa chỉ, họ tên, CCCD…; tìm theo tên cột trong mọi file `.sql`). Số này đã kiểm chéo bằng 2 cách (bộ quét và tìm tên cột rồi đọc tay) và ra gần như nhau (33/35 và 32/35).
- **X và Z thấp sau khi kiểm tay**: corpus phần lớn là app quản lý nội bộ, bán hàng, đặt lịch, ít app gửi dữ liệu cá nhân sang AI. Nhưng **31% repo đã gọi AI nước ngoài** — chỉ là bộ quét chưa chứng minh được dữ liệu cá nhân đi theo lời gọi đó.
- **C3 của cả 35 repo là `CAN_NGUOI_XAC_NHAN`**: repo công khai không cho biết loại hình doanh nghiệp hay số người dùng, nên không chốt được miễn trừ.
- **Bộ quét báo nhầm nhiều ở phân loại tên cột** (6/9 cờ "nhạy cảm" sai) → khớp đúng pain mà metric `phan_loai_viet_tat` và `bao_dong_gia` muốn đo. Lỗi C1 (chuỗi chữ bị tính là lời gọi) và consent bị sót đã sửa ở PR #11; cờ phân loại tên cột giữ nguyên ở chế độ `rule` để làm đường so sánh cho ablation.

## 4. ≥5 ví dụ cụ thể (mã đã ẩn danh)

**Đúng (kiểm tay xác nhận):**
1. repo-01 (quản lý phòng khám): bảng phiếu khám có cột `diagnosis` → tình trạng sức khoẻ (ND356 Điều 4.1 điểm d).
2. repo-45 (phòng khám nhiều bác sĩ): `prescriptions.diagnosis`, `visits.diagnosis_code`, `visits.diagnosis_name` → tình trạng sức khoẻ.
3. repo-14 (nền tảng gia sư): route gửi email tư vấn `fetch('https://api.resend.com/emails', …)` kèm email của gia sư (`tutors.email`) → dữ liệu cá nhân đi tới dịch vụ email nước ngoài (C1).
4. repo-17: có bảng `consents` (`user_id`, `granted_at`, `policy_version`, `purpose`, `withdrawn_at`…) — một trong **2/35** repo có nhật ký đồng ý gần đủ (repo kia: repo-02, bảng `dong_y_du_lieu`).

**Cần người xem:**

5. repo-41: bảng kết nối cổng thanh toán lưu số tài khoản, tên chủ tài khoản ngân hàng của người bán, kèm webhook nhận giao dịch → có thể thuộc ND356 Điều 4.1 điểm k (thông tin tài khoản, lịch sử giao dịch).

**Báo nhầm (bộ quét gắn cờ, kiểm tay thấy sai):**

6. repo-24 `repair_orders.diagnosis` và repo-51 `quotes.diagnosis`: chẩn đoán lỗi **thiết bị** trong đơn sửa chữa / báo giá, không phải sức khoẻ.
7. repo-02 `seo_*.vi_tri`: **vị trí xếp hạng SEO**, không phải vị trí của người.
8. repo-20 `vitricongviec`: **vị trí công việc** (chức danh).
9. repo-10 `clubs.latitude`, repo-27 `cafes.latitude`: toạ độ của **câu lạc bộ, quán cafe**, không phải của cá nhân.
10. repo-22: chuỗi chữ nhắc tới Mailchimp trong script sinh tài liệu bán hàng, không phải lời gọi API.

## 5. Giới hạn của data

- Chỉ repo **công khai** → lệch về dự án học tập, portfolio, đồ án. App thương mại của freelancer thường để private.
- **Phân tích tĩnh**: thấy lời gọi ra ngoài trong code, không biết app có thật sự chạy và gửi dữ liệu thật không. Không gọi endpoint, không chạy app.
- Bộ dò sink và consent dùng quy tắc (regex) → có thể sót lời gọi qua wrapper tự viết, hoặc sót bảng consent đặt tên lạ.
- **Số Y chỉ dựa trên schema SQL**: cả bộ quét lẫn cách đếm tay chỉ đọc file `.sql`. Sự đồng ý có thể được lưu ở chỗ khác — `auth.users.raw_user_meta_data` của Supabase (JSON, không có trong migration), cookie banner / localStorage phía trình duyệt, hoặc công cụ bên ngoài (CMP, form của bên thứ ba). Vì vậy 32/35 có thể **hơi cao** so với thực tế; con số đúng nghĩa là "32/35 repo không có chỗ lưu đồng ý **trong schema**".
- Lọc "người Việt" bằng chữ riêng của tiếng Việt → bỏ sót repo viết hoàn toàn bằng tiếng Anh.
- Mẫu không ngẫu nhiên: 5 repo chọn tay, 30 repo theo thứ tự kết quả tìm kiếm (ưu tiên repo khớp chuỗi tiếng Việt trong code, rồi repo cập nhật gần đây).
- Chỉ kiểm tay các repo **bị gắn cờ** → biết bộ quét báo nhầm bao nhiêu, nhưng chưa biết nó **bỏ sót** bao nhiêu ở X và Z (trừ Y đã kiểm chéo). Kiểm ngẫu nhiên 5–10 repo không bị gắn cờ là việc tiếp theo.
- Tín hiệu "do AI sinh" (lovable, bolt.new, cursor…) chỉ thấy ở **2/35** repo → không đủ để so app do AI sinh với app tự viết.
- Data cho biết người ta **làm gì**, không cho biết **vì sao** (không biết hay biết mà bỏ qua).
  → Kiểm lại bằng phỏng vấn freelancer (`evidence/interviews/`).
