# Khai báo dùng AI

README của nhóm có mục "Dùng AI vào việc gì" (2–3 dòng, bắt buộc). Ghi chi tiết vào bảng dưới đây.

> Luật của đề: dùng AI để làm bài thoải mái, nhưng **ai không giải thích được phần có tên mình thì phần đó nhận 0 điểm**. Khai thiếu không bị trừ; giấu mới bị.

| Việc | Công cụ AI | AI làm gì | Người kiểm/sửa gì | Ai phụ trách |
|---|---|---|---|---|
| Code bản chạy thử | Claude Code | Viết scanner, classify, verify, rule engine, `agent.answer()`, web demo và test theo kế hoạch nhóm đã soạn | Minh đọc và chạy lại từng module, review chéo qua PR; mọi PR có người khác duyệt trước khi merge | Minh (pipeline), Thắng (FE web) |
| Prompt / thiết kế lời gọi mô hình | Claude Code | Soạn nháp prompt phân loại cột và prompt kiểm chứng đường đi | Minh sửa theo lỗi lượt 1 (PR #15); Thịnh review, thêm test giữ quy tắc prompt; Khoa chọn phương án (b) ở PR #23 sau khi đo, không merge các bản prompt không hơn mốc (`spec.md` §10) | Minh |
| Bảng luật JSON (`data/legal/`) | Claude Code (soạn), Codex (review chéo) | Gợi ý cấu trúc JSON, trích khoản từ văn bản đã crawl | Khoa đối chiếu **từng mã điều khoản** với văn bản gốc Luật 91, Nghị định 356, Nghị định 330; không dùng trích dẫn do AI sinh mà không kiểm | Khoa |
| Đào data (viết script đếm, gợi ý nhãn) | Claude Code | Viết `scripts/crawl_corpus.py`, `scan_corpus.py` | Kiểm tay từng repo bị gắn cờ trong 35 repo; số máy đếm chỉ dùng để thống kê, không làm nhãn (`evidence/summary.md` mục 2.2) | Thắng |
| Rà câu hỏi phỏng vấn / khảo sát | — | Không dùng | — | Thắng |
| Viết câu thử (benchmark) | Claude Code | Hỗ trợ soạn kịch bản 60 case theo bảng phân bổ ô `nhom_con` | Thịnh dán nhãn; nhãn commit trước commit đầu của `codebase/rules.py`; mỗi câu thử có `source` (`tu_viet` / `data_that`) | Thịnh |
| Sinh data `synthetic` (nếu có) | Claude Code | Như dòng trên; không sinh bằng script ngẫu nhiên | Seed: không có (viết tay) · `validate_cases.py` kiểm cấu trúc và quét giá trị thật; Minh, Khoa review ở PR #5 | Thịnh |
| Chấm cột `pass` bằng LLM (nếu có) | — | Không dùng; chấm bằng code `eval/grade.py` | — | Thịnh |

**Không dùng AI để:** tạo người được phỏng vấn, trích dẫn, câu trả lời khảo sát; sửa kết quả các lượt đã chạy (`eval/run-*.csv`, `cost/simulate-*.csv`, `traces/`).
