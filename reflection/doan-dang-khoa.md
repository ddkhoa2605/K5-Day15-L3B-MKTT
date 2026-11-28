# Reflection — Đoàn Đăng Khoa

> Làm ở guide bước 5.3. Mỗi người một file: chép file này thành `reflection/<ten-khong-dau>.md` (viết thường, không dấu). Hạn: **23:59 Thứ Bảy 28/11**. Mỗi câu 3–6 dòng.

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   Đội trưởng nhóm MKTT. Tôi dựng bảng luật JSON `data/legal/*.json` (nhóm nhạy cảm, miễn trừ, trích dẫn, mức phạt: `2df0010`, `e0b9749`, đối chiếu Nghị định 330 ở `e68645d`), chốt 4 metric và chuẩn "đạt" trước CP2 (`eval/metric_spec.yaml`, `spec.md` §7, `a799ce2`), viết `spec.md` và `canvas.md` (`7c6825b`, `d452946`).
   Sau lượt 1, tôi chốt hai giả định C1 (người nhận email qua dịch vụ nước ngoài) và C3 (cột chữ tự do) (`ae711b5`), chọn phương án (b) ở PR #23 và làm phần cơ học của #24 (`b677df6`). Tôi cũng viết trước cách đọc kết quả bộ mù (`d7444c4`), chạy `simulate-1` và điền `cost/cost-estimate.md` (`f729577`), làm slide, thuyết trình, nộp các checkpoint và duyệt merge PR của nhóm.

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   Tôi dùng Claude Code để soạn nháp bảng luật JSON, `spec.md`, báo cáo, và dùng Codex để review chéo bảng luật. Chỗ tôi không tin AI là mã điều khoản: tôi đối chiếu từng mã với văn bản gốc Luật 91, Nghị định 356. Nghị định 330 chỉ có bản tin của EY, nên tôi để `can_cu: []` thay vì để AI điền số điều, rồi bổ sung dần sau khi đối chiếu (`e68645d`, `e0b9749`, `0e506fb`).


3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   Câu `dt-r02-004` (code thật): component gửi `name: user.full_name` lên route server, route đưa họ tên vào system prompt rồi gọi Claude của Anthropic. Hệ thống trả C1 = `KHONG_KICH_HOAT` ở cả bốn lượt, trong khi nhãn là `KICH_HOAT`. Đây là lỗi nguy hiểm nhất của sản phẩm: người dùng tin kết quả "sạch" rồi bỏ sót nghĩa vụ chuyển dữ liệu xuyên biên giới.
   Lượt 2 tăng từ 70% lên 80% làm cả nhóm tưởng đã sửa được lỗi, nhưng phân tích lại thì phần tăng đến từ nhóm lỗi gắn nhầm `hanh_vi_mang` trên câu tự viết, còn 4/5 câu bỏ sót C1 trên code thật vẫn trượt. Tôi học được hai điều. Thứ nhất, phải xem số theo từng nhóm lỗi và theo nguồn (tự viết hay code thật), không chỉ nhìn % tổng. Thứ hai, chỉ khi giữ nguyên chuẩn "đạt" và ghi thật thì nhóm mới thấy rõ chỗ chưa làm được.
