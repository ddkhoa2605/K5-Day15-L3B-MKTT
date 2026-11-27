# Khảo sát — bộ câu hỏi, kênh gửi, thời gian

## Kênh và thời gian
- **Kênh:** Google Form
- **Mở:** khoảng 17:00 Thứ Sáu 27/11/2026. **Đóng:** khoảng 05:00 Thứ Bảy 28/11/2026. Phản hồi cuối cùng ghi nhận lúc khoảng 22:50 27/11.
- **Người trả lời:** người ngoài nhóm (bạn bè đại học, học viên khoá AI20K), có dựng hoặc tham gia dựng app. Không có thành viên nhóm MKTT.
- **Số phản hồi:** 31. Câu 1 lọc người dùng: **27 người** trả lời "Có" (đã dựng app trong 12 tháng qua). 4 người trả lời "Không" bỏ trống các câu sau, nên mọi số ở `evidence/summary.md` mục 2.4 tính trên **n = 27**.
- **Dữ liệu:** `results.csv` là bản đã bỏ cột email và thay dấu thời gian bằng khung 3 giờ; thứ tự dòng đã xáo. Bản xuất gốc có email **không commit** (đã gitignore).
- **Ngưỡng:** khảo sát **không** đặt ngưỡng "mình đúng nếu…" trước khi gửi, nên chỉ dùng để mô tả, không phải kiểm định giả thuyết. Phần kiểm định đặt trước nằm ở `evidence/hypothesis.md` mục 2b (phỏng vấn, chưa làm).

## Câu hỏi

Đặt tên câu theo thứ tự trên form. Các lựa chọn ghi dưới đây là các lựa chọn **xuất hiện trong kết quả**; form có thể có thêm lựa chọn không ai chọn.

| # | Câu hỏi (nguyên văn) | Kiểu | Lựa chọn thấy trong kết quả |
|---|---|---|---|
| 1 | Trong 12 tháng qua, bạn có dựng hoặc tham gia dựng app web/mobile có người dùng tại Việt Nam không? | Chọn một | Có · Không |
| 2 | Vai trò chính của bạn khi dựng app là gì? | Chọn một | Lập trình viên trong doanh nghiệp · Freelancer · Agency/studio · Tech lead/CTO startup · Khác |
| 3 | App gần nhất của bạn (hoặc của khách) thuộc loại hình nào? | Chọn một | Cá nhân, chưa đăng ký kinh doanh · Hộ kinh doanh · Doanh nghiệp siêu nhỏ · Doanh nghiệp nhỏ/khởi nghiệp · Doanh nghiệp vừa hoặc lớn · Không rõ |
| 4 | Tính từ trước đến nay, app lớn nhất của bạn đã có tổng cộng bao nhiêu người dùng? | Chọn một | Dưới 1.000 · 1.000–10.000 · 10.000–100.000 · Không rõ |
| 5 | App gần nhất thu hoặc lưu những thông tin nào của người dùng? | Chọn nhiều | Họ tên, email, số điện thoại · Chat, nhật ký, ghi chú riêng tư · Theo dõi hành vi (event tracking, analytics) · Vị trí GPS, "tìm gần tôi", bản đồ · Thẻ, ví, lịch sử giao dịch · Khuôn mặt, vân tay, eKYC · Sức khỏe, giấc ngủ, lịch khám · Không thu thông tin cá nhân · Không rõ |
| 6 | App có gửi hoặc lưu dữ liệu người dùng ở dịch vụ nước ngoài nào không? | Chọn nhiều | API AI (OpenAI, Anthropic, Gemini…) · Database hoặc server đặt ở nước ngoài · Gửi email (SendGrid, Resend…) · Analytics (Google Analytics, Mixpanel, PostHog…) · Không · Không rõ |
| 7 | App xin sự đồng ý của người dùng bằng cách nào? | Chọn một | Lưu vào database kèm thời gian và phiên bản chính sách · Ghi "tiếp tục sử dụng nghĩa là đồng ý" · Checkbox đã tích sẵn · Không xin · Không rõ |
| 8 | Trước khi phát hành, bạn thường kiểm tra những gì? | Chọn nhiều | Bảo mật, lộ secret/API key · Trang chính sách quyền riêng tư · Tuân thủ pháp luật về dữ liệu · Không kiểm tra gì · Khác |
| 9 | Bạn biết đến đâu về Luật Bảo vệ dữ liệu cá nhân 91/2025 và các nghị định hướng dẫn (356/2025, 330/2026)? | Chọn một | Chưa nghe · Nghe tên · Biết sơ qua · Hiểu khá rõ · Đã áp dụng vào app |
| 10 | Tôi lo ngại app mình làm có thể đang chưa đáp ứng quy định về dữ liệu cá nhân. | Thang 1–5 | 1 … 5 |
| 11 | Bạn đã bao giờ hỏi chatbot AI về nghĩa vụ pháp lý liên quan đến dữ liệu chưa? | Chọn một | Chưa bao giờ · Có, và thấy hữu ích · Có, nhưng không chắc nó đúng · Có, và sau đó phát hiện nó sai |
| 12 | Công cụ được mô tả ở trên hữu ích với công việc của bạn đến mức nào? | Thang 1–5 | 1 … 5 |
| 13 | Bạn thấy những tính năng nào quan trọng nhất? (chọn tối đa 3) | Chọn nhiều | Chỉ ra dòng code làm bằng chứng · Trích đúng số điều, khoản · Không gửi code ra nước ngoài · Cảnh báo mất miễn trừ · Báo khi nào cần luật sư · Sinh hồ sơ nháp .docx |
| 14 | Mức giá mỗi tháng bạn thấy hợp lý là bao nhiêu? | Chọn một | Chỉ dùng nếu miễn phí · Dưới 200.000 đ · 200.000–500.000 đ |
| 15 | Ai sẽ quyết định chi tiền cho công cụ này? | Chọn một | Tôi · Khách hàng của tôi · Founder/CEO · Bộ phận pháp chế · Không rõ |
| 16 | Nếu được dùng thử, điều gì sẽ khiến bạn tiếp tục dùng công cụ này? | Đoạn văn (không bắt buộc) | — |

Đoạn mô tả công cụ hiện trước câu 12 trên form: *Một công cụ quét mã nguồn app trước khi phát hành. Nó chỉ ra app đã phát sinh nghĩa vụ nào theo Luật Bảo vệ dữ liệu cá nhân, kèm dòng code làm bằng chứng, điều luật làm căn cứ và hồ sơ nháp .docx. Gặp trường hợp chưa rõ, nó báo "cần luật sư rà soát"*.

## Lưu ý khi đọc
- Câu 1–11 hỏi về **việc đã làm** hoặc hiểu biết hiện tại, nên là phần dùng làm bằng chứng pain.
- Câu 12–16 hỏi **ý kiến sau khi đọc mô tả sản phẩm**, nên chỉ là tín hiệu yếu về nhu cầu và giá, không phải bằng chứng pain.
- Mọi câu đều là **tự khai**: người trả lời có thể không biết chính xác app của mình gửi gì ra ngoài hay lưu đồng ý thế nào.
