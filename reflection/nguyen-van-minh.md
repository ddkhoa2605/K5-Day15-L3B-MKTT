# Reflection — Nguyễn Văn Minh

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   Thành viên, dev pipeline trong `codebase/`: `legal.py`, `scanner.py` (schema, sink, consent, lọc secret), `classify.py` + `verify.py`, rule engine C1/C2/C3 `rules.py`, và `agent.py` với 3 chế độ `rule` / `hybrid` / `llm` (`2609dcf`, `016e77b`, `9f37f6e`, `bbe1055`).
   Nối model thật qua `ai.py`: OpenAI `gpt-6-luna` để phân loại, `gpt-6.1-terra` để kiểm chứng, token lấy từ `usage` (`40a010e`, PR #8, `d5bc66f`).
   Sau lượt 1: sửa prompt cho cột thời gian (`3767012`), lần theo dữ liệu qua biến trung gian và hàm bọc (`792866d`), làm theo 2 quy tắc Khoa chốt (`19c22c1`). Làm backend web cho demo LexTrace (`d0b76f3`).
   Review PR #5 của Thịnh, bắt được nhãn C2 sai ở `dt-r02-001`.

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   Dùng Claude Code để lập kế hoạch M1–M6 (`docs/superpowers/plans/2026-11-27-ship-hop-phap.md`), viết code + test và tóm tắt tiến độ (`docs/minh-summary.md`). GPT nằm ngay trong sản phẩm, làm hai việc: phân loại cột và kiểm chứng đường đi dữ liệu.
   Chỗ phải sửa: review của Khoa bắt các lỗi an toàn mà bản đầu chưa có, như chưa thử lại khi API lỗi tạm thời, API key có thể lộ, và lượt bị từ chối chưa huỷ kết luận đang chờ (`5aeaa2d`, `d5bc66f`).
   Ở phía model: `gpt-6-luna` xếp `created_at`, `gio_bat_dau` vào nhóm `hanh_vi_mang` nên C3 sai thành `MAT_MIEN_TRU`. Mình sửa prompt bằng một quy tắc chung, không so khớp câu thử, rồi kiểm trên repo demo nằm ngoài benchmark (`3767012`).
   Bài học: AI viết nhanh nhưng các biên an toàn (secret, mã luật bịa, hành động ra ngoài) phải tự kiểm và phải có test.

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   `dt-r02-001` trượt cả 4 lượt. App gửi nguyên file ghi âm cuộc gọi của khách (base64) sang Gemini. Scanner có thấy sink `lib/cuoc-goi-chep.ts:18`, nhưng bước kiểm chứng trả `xac_nhan: False, truong_ca_nhan: []` (`traces/run-4.jsonl`): trong lời gọi chỉ có biến `b64`, không có cột nào, nên model không nối được tới dữ liệu cá nhân. Lời gọi thứ hai sang Anthropic (`lib/cham-chat-sale.mjs:46`, gửi bản chép lời) thì scanner không nhận ra là sink, vì đoạn code chỉ có `model: "claude-haiku-5-5"`, không có URL hay SDK. Kết quả là C1 ra `KHONG_KICH_HOAT`.
   C2 cũng sai: repo có bảng `dong_y_du_lieu` đủ trường nên hệ thống coi là đã có đồng ý, trong khi bảng đó chỉ form lead ghi vào, không phải đồng ý của khách bị ghi âm.
   Học được: dữ liệu cá nhân còn nằm trong file âm thanh và ảnh, không chỉ trong cột. Đồng ý cũng phải đúng chủ thể, đúng luồng. Quan trọng nhất: khi đã thấy sink nước ngoài mà không xác nhận được đường đi, hệ thống nên trả `CAN_NGUOI_XAC_NHAN`, không trả `KHONG_KICH_HOAT`. Báo "an toàn" sai là lỗi nguy hiểm nhất với người dùng.
