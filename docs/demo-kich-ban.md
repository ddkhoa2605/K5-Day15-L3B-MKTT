# Kịch bản demo Lextrace (khoảng 3–4 phút)

> **Lextrace** đọc mã nguồn app Next.js + Supabase và chỉ ra app đã phát sinh nghĩa vụ dữ liệu cá nhân nào (C1, C2, C3), kèm dòng code làm bằng chứng và điều luật làm căn cứ. Kết quả là gợi ý để người chịu trách nhiệm xác nhận, **không phải ý kiến pháp lý**.

Mọi bước dưới đây đã được bấm thử trên Chrome ngày 28/11 (repo A, B, C; file .zip; JSON; model thật).

---

## 0. Chuẩn bị (làm trước khi lên, mất khoảng 5 phút)

1. **Lấy code mới nhất.** Nếu PR #28 đã merge vào `main`:
   ```bash
   git checkout main && git pull
   ```
   Nếu PR #28 chưa merge:
   ```bash
   git fetch origin && git checkout thang/ui-noi-api && git pull
   ```
2. **Kiểm file `.env`** ở gốc repo có API key (không mở file ra màn hình chiếu).
3. **Bật server:**
   ```bash
   SHP_UI=web python3 run.py
   ```
   Trên Windows (PowerShell): `$env:SHP_UI="web"; python run.py`
4. **Mở trình duyệt ở cửa sổ ẩn danh**, vào `http://127.0.0.1:8000`.
   - Cửa sổ ẩn danh để trang không nhớ phiên thử trước đó.
   - Phóng to chữ (Cmd/Ctrl +) cho người ngồi xa đọc được.
5. **Chạy thử repo B một lần** (Cảnh 1 bên dưới) để chắc model gọi được, rồi đóng cửa sổ, mở cửa sổ ẩn danh mới.

> Báo lỗi cổng bận (`Address already in use`): thêm `SHP_PORT=8001` vào lệnh và mở `http://127.0.0.1:8001`.

---

## Cảnh 1: repo B — AI có kiểm soát, bắt được dữ liệu gửi ra nước ngoài (khoảng 1 phút 30)

**Bối cảnh repo B:** app có chatbox gọi OpenAI. Code nhét tên và email khách vào câu hỏi gửi cho OpenAI.

| Bấm gì | Nói gì |
|---|---|
| Trang đầu: tab **Repo demo**, ô chọn **repo_b**. Kéo xuống thấy nút **hybrid** đang sáng (mặc định). | "Đây là một app thật kiểu freelancer hay làm: Next.js, Supabase, có chatbox AI." |
| Bấm **Quét mã nguồn** (góc phải dưới). | "Bước này chỉ đọc code, **chưa gọi AI**." |
| Màn **xem trước**: chỉ vào khung đen bên phải "Sẽ gửi cho model AI". Kéo xuống tới đoạn code. | "Trước khi gọi AI, hệ thống cho xem **đúng và đủ** những gì sẽ gửi đi: tên cột và đoạn code quanh lời gọi ra ngoài, đã che API key. **Không gửi dữ liệu trong bảng.**" |
| Chỉ vào dòng `` content: `Khách ${profile.ho_ten} (${profile.email}) hỏi: ...` `` | "Đây là chỗ đáng chú ý: tên và email khách đi thẳng vào câu hỏi gửi OpenAI." |
| Bấm **Gửi kiểm tra**. Chờ khoảng 5–10 giây. | "Giờ mới gọi AI: một model phân loại tên cột, một model kiểm chứng đường đi dữ liệu." |
| Màn **kết quả**: thẻ **C1** có nhãn đỏ **"Đã phát sinh"**. | "C1, chuyển dữ liệu ra nước ngoài: **đã phát sinh**. Phải lập hồ sơ đánh giá tác động trong **60 ngày** kể từ lần chuyển đầu tiên, căn cứ Điều 20 Luật 91. Có mức phạt tham khảo." |
| Bấm **Bằng chứng (1)** ở thẻ C1. | "Bằng chứng trỏ đúng file và dòng code, người review mở ra kiểm được ngay." |
| (Tuỳ chọn) chỉ dòng chữ phía dưới phần căn cứ. | "**Số điều luật do rule engine chọn từ bảng có sẵn, AI không được tự viết số điều.** Đây là chỗ chống bịa." |

Kết quả mong đợi: C1 **Đã phát sinh** · C2 **Không phát sinh** · C3 **Cần bạn xác nhận**.

---

## Cảnh 2: repo C — hỏi đúng thứ code không biết, rồi kết luận mất miễn trừ (khoảng 1 phút)

**Bối cảnh repo C:** app đặt sân thể thao, lưu **vị trí gần nhất** của người dùng (dữ liệu nhạy cảm) và có ô đồng ý **tích sẵn**.

> ⚠️ **Chạy cảnh này ở chế độ `rule`.** Ở chế độ hybrid, model có lúc (khoảng một nửa số lần thử) xếp cột `vi_tri_gan_nhat` là "chưa rõ", nên C3 dừng ở "Cần bạn xác nhận" thay vì "Mất miễn trừ". Chế độ rule ra đúng mọi lần. Cách trình bày tự nhiên: giới thiệu chế độ rule là **chế độ riêng tư, không gửi gì ra ngoài**.

| Bấm gì | Nói gì |
|---|---|
| Quay về trang đầu (bấm logo **Lextrace**). Chọn **repo_c**, kéo xuống bấm **rule**. | "Doanh nghiệp không muốn gửi gì ra ngoài thì dùng chế độ rule: chỉ luật viết tay, **không gọi AI, không gửi gì**." |
| Bấm **Quét mã nguồn**. Màn xem trước ghi "Không gửi gì". Bấm **Chạy kiểm tra**. | |
| Màn kết quả: C2 nhãn đỏ đậm **"Đã phát sinh, cách xin sai"**. | "C2: có xin đồng ý nhưng **ô đồng ý tích sẵn**, không hợp lệ theo Nghị định 356." |
| C3 nhãn cam **"Cần bạn xác nhận"**. | "C3 là miễn trừ cho doanh nghiệp nhỏ. Code không cho biết công ty lớn hay nhỏ, nên hệ thống **không đoán mà hỏi lại**." |
| Ở ô cam phía trên: **Loại hình tổ chức** chọn **Doanh nghiệp siêu nhỏ**, **Số chủ thể** gõ **4200**, bấm **Cập nhật kết luận**. | "Giả sử đây là công ty siêu nhỏ, mới có 4.200 người dùng." |
| C3 chuyển thành nhãn đỏ **"Mất miễn trừ"**. | "Dù siêu nhỏ, app **vẫn mất miễn trừ** vì trực tiếp xử lý vị trí người dùng, là dữ liệu nhạy cảm. Bước này **không gọi lại AI**, chỉ chạy lại luật." |
| (Tuỳ chọn) Bấm **Bằng chứng (1)** ở C3. | "Bằng chứng là dòng 19 của file schema: cột `vi_tri_gan_nhat`." |

Kết quả mong đợi: C1 **Không phát sinh** · C2 **Đã phát sinh, cách xin sai** · C3 **Cần bạn xác nhận** → sau khi khai → **Mất miễn trừ**.

---

## Cảnh 3: cổng duyệt và hồ sơ nháp (khoảng 30 giây)

| Bấm gì | Nói gì |
|---|---|
| Bấm **Sang cổng duyệt** (góc phải dưới). | "Kết quả không tự đi đâu cả. Phải có **người chịu trách nhiệm** duyệt." |
| Tích ô từng phát hiện, gõ tên (ví dụ "Nguyen Van A"), chọn vai trò **Tech lead**, tích "Tôi đã đọc bằng chứng…". Nút **Xác nhận kết luận** sáng lên, bấm. | "Nút chỉ bật khi đã đọc từng phát hiện." |
| Màn **hồ sơ nháp**: chỉ nhãn **BẢN NHÁP · chưa được luật sư rà soát** và các ô cam **[CẦN ĐIỀN]**. | "Hệ thống soạn sẵn hồ sơ nháp. Những gì code không biết, như mục đích xử lý hay thời gian lưu, **để trống chứ không bịa**. Có nút tải về, **không có nút gửi** cơ quan nào." |

---

## Cảnh phụ (nếu còn thời gian): repo A — không báo động giả

Chọn **repo_a**, hybrid, quét rồi gửi kiểm tra. App này cũng gọi AI nhưng **không gửi dữ liệu cá nhân**, nên C1 ra **Không phát sinh**.
Câu nói: "Không phải app nào có AI cũng bị báo đỏ. Hệ thống phân biệt được."

---

## Số liệu để trả lời câu hỏi

| Nội dung | Số | Nguồn |
|---|---|---|
| Benchmark 30 câu (hybrid) | run-1: 21/30 · run-2: 24/30 · run-3: 24/30 · run-4: 23/30 | `eval/README.md`, PR #26 |
| Chuẩn "đạt" nhóm tự đặt (≥ 80% **và** trích dẫn đúng 100%) | **Chưa đạt**: trích dẫn đúng 17/21 (81%) | PR #26 |
| Câu nhóm tự viết / câu từ code thật | 17–18/18 · 6/12 | PR #26 |
| Từ chối đúng khi thiếu căn cứ | 14/14 | PR #26 |
| AI làm một mình (không rule engine), 50 câu dev | 0/50; có danh sách mã điều luật vẫn chỉ 1/50 | PR #23, `spec.md` §10 |
| Holdout cũ, 10 câu, chạy một lần | hybrid 8/10 · rule 8/10 · AI một mình 0/10 | PR #19 |
| Bộ mù 12 câu | xem số Khoa tổng hợp (Thịnh chạy sau khoá code) | issue #20 |
| Chi phí một lượt quét | 1–2 lần gọi model, dưới 3.000 token, 4–8 giây | thử ngày 28/11 |

---

## Câu hỏi hay gặp

**"Có chính xác không?"**
→ "Trên benchmark 30 câu, đạt 23–24 câu, **chưa đạt chuẩn nhóm tự đặt**. Chỗ yếu là code thật khi dữ liệu đi qua nhiều file, hệ thống chỉ thấy một đoạn. Bù lại, khi không chắc, hệ thống **hỏi người**, không kết luận bừa (từ chối đúng 14/14)."

**"Sao không để AI làm hết cho nhanh?"**
→ "Nhóm đã đo: AI làm một mình, kể cả model mạnh nhất và có sẵn danh sách điều luật, chỉ đúng 0–1 trên 50 câu và hay bịa số điều. Nên AI chỉ làm việc nó giỏi (đọc tên cột viết tắt, đọc code), còn kết luận pháp lý do rule engine."

**"Gửi code của tôi cho AI có an toàn không?"**
→ "Trước khi gửi, màn xem trước hiện **toàn bộ** nội dung sẽ gửi: chỉ tên cột và đoạn code quanh lời gọi ra ngoài, đã che key. Không gửi dữ liệu trong bảng. Không muốn gửi gì thì dùng chế độ rule."

**"Kết quả này dùng nộp cơ quan được không?"**
→ "Không. Đây là gợi ý để người chịu trách nhiệm xác nhận, hồ sơ chỉ là bản nháp, cần luật sư rà soát. Nhóm cũng chưa nhờ luật sư duyệt các giả định."

**"Nếu C3 ra 'Cần bạn xác nhận' trong khi bạn mong 'Mất miễn trừ'?"** (lỡ chạy repo C ở hybrid)
→ Đọc phần giải thích: "Có cột chưa xác định được nhóm dữ liệu (`bookings.vi_tri_gan_nhat`)". Nói: "Đây là lúc AI không chắc nên hệ thống **dừng lại hỏi người** thay vì đoán. Chạy chế độ rule để thấy kết luận theo từ khoá." Rồi làm lại cảnh 2 ở chế độ rule.

---

## Sự cố và cách xử lý

| Sự cố | Làm gì |
|---|---|
| Mất mạng / model báo lỗi | Chuyển sang chế độ **rule** (kéo xuống ở trang đầu). Cảnh 2 và 3 chạy được hoàn toàn không cần mạng. |
| Trang trắng | Tắt server, chạy lại với giao diện dự phòng: `SHP_UI=web SHP_WEB_DIR=web python3 run.py`. Bản này là một file, cùng luồng. |
| Báo cổng bận | Thêm `SHP_PORT=8001`, mở `http://127.0.0.1:8001`. |
| Trang hiện kết quả cũ | Bấm logo **Lextrace** để về trang đầu, hoặc mở cửa sổ ẩn danh mới. |
| Gửi kiểm tra chờ quá 30 giây | Tải lại trang, quét lại. Nếu vẫn treo, chuyển sang chế độ rule. |

---

## Checklist 1 phút trước khi lên

- [ ] Server đang chạy, trang mở ở cửa sổ ẩn danh, đã phóng to chữ
- [ ] Đã chạy thử repo B ở hybrid thành công một lần
- [ ] Nhớ: **repo B dùng hybrid, repo C dùng rule**
- [ ] Không mở `.env` hay terminal có key trên màn hình chiếu
- [ ] Thuộc 3 câu chốt: *xem trước những gì gửi đi* · *AI không viết số điều luật* · *chỉ là bản nháp, người duyệt chịu trách nhiệm*
