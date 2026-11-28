# Cách đọc kết quả bộ mù (viết trước khi chạy)

> Ghi lúc 07:03 ngày 28/11 (giờ commit `d7444c4`), **trước** khi khoá code (12:00) và trước khi chạy bộ mù; manifest đã khoá lúc 06:58 (commit `b7d8141`). Khoa chốt. Sau khi chạy, báo cáo theo đúng các quy tắc dưới đây; không đổi quy tắc theo kết quả. Bộ mù: 12 câu, sha256 trong `eval/blind.manifest`, giao việc ở issue #20.

## 1. Chạy gì, báo gì
- Ba cấu hình chạy **một lần**, cùng commit `code-freeze`: A (rule), C (hybrid, cấu hình mặc định), B (chỉ LLM, **bản có danh sách mã đóng**, `SHP_LLM_CODES=closed`, model mạnh nhất). B nguyên bản không chạy trên bộ mù vì khoá chỉ cho một lần chạy; việc B nguyên bản tự bịa mã đã đo trên dev (50/50 câu có mã ngoài bảng luật).
- Mỗi cấu hình báo: số câu đạt k/12 kèm khoảng Wilson 95%, bốn metric (k/n), danh sách câu trượt kèm nguyên nhân. Chấm bằng `eval/grade.py` không sửa.
- Câu có lỗi hạ tầng (cột `error` khác rỗng) sau một lần chạy lại theo issue #20 vẫn lỗi thì tính là **trượt** và ghi riêng.
- Cỡ mẫu nhỏ: metric có n < 10 (`SMALL_N` của `grade.py`) chỉ báo k/n, **không** kết luận đạt hay chưa đạt. Trên bộ này gồm `phan_loai_viet_tat` (n = 1) và `bao_dong_gia` (n = 4).

## 2. So A với C (rule với hybrid)
So **từng câu** trên cùng 12 câu. Đếm g = số câu C đạt mà A trượt, l = số câu A đạt mà C trượt.

| Kết quả | Cách nói |
|---|---|
| g − l ≥ 2 | "Trên code chưa thấy, hybrid **gợi ý** có thêm giá trị (hơn g − l câu trên 12); n nhỏ nên chưa chứng minh được." |
| −1 ≤ g − l ≤ 1 | "Rule và hybrid **ngang nhau** trên code chưa thấy. Khuyên dùng rule làm mặc định (miễn phí, lặp lại được), hybrid là tuỳ chọn khi rule báo không rõ." |
| l − g ≥ 2 | "Trên code chưa thấy, **rule tốt hơn** hybrid (l − g câu trên 12). Bước AI hiện chưa nên bật mặc định." |

Trong mọi trường hợp: nêu đủ g và l, không chỉ hiệu số; không dùng chữ "có ý nghĩa thống kê". Ngưỡng 2 câu là ngưỡng thực dụng Khoa chốt trước khi chạy, không phải kiểm định: với n = 12 không mức chênh nào chứng minh được gì.

## 3. So B với C (chỉ LLM với hybrid)
| Kết quả | Cách nói |
|---|---|
| B thấp hơn cả A và C từ 4 câu trở lên | Giữ luận điểm "LLM không tự quyết được; cần bảng luật đóng và rule engine". |
| B kém C 2–3 câu | Nói "B kém hơn", kèm số; không nói "LLM không làm được". |
| B trong khoảng 1 câu của C, hoặc hơn C | **Rút lại** luận điểm "cần rule engine" cho bộ này; nói đúng con số. |

Vì B đã được cho danh sách mã đóng, chênh lệch B–C ở đây đo khả năng **áp luật**, không đo việc bịa mã. Vẫn báo số mã ngoài bảng luật nếu có.

## 4. Chuẩn "đạt"
Áp đúng nguyên văn `spec.md` §7 cho cấu hình C. Chưa đạt thì ghi "chưa đạt chuẩn trên bộ mù"; **không** đổi chuẩn, không chọn tập con để đạt.

## 5. So với các số trước
Đặt cạnh: benchmark 30 (run-1 21/30, run-2 24/30, run-3/4 khi có), phần code thật của benchmark (hybrid 6/12, rule 5/12), holdout cũ (A 8/10, C 8/10, B 0/10), dev 50 (hybrid 42–47/50).
- C trên bộ mù **≤ 7/12** trong khi dev khoảng 90% → nói "số dev lạc quan vì đã chỉnh theo dev; số bộ mù là số đúng để dùng".
- C trên bộ mù gần với phần code thật của benchmark (khoảng 50–60%) → nói "khớp với số code thật trước đó".

## 6. Phân loại câu trượt
Mỗi câu trượt gán đúng một nguyên nhân chính:
1. **Quét:** scanner không thấy lời gọi ra ngoài hoặc cột.
2. **Phân loại cột:** nhóm nhạy cảm sai hoặc thiếu.
3. **Kiểm chứng đường đi:** kết luận sai về việc có gửi dữ liệu cá nhân ra ngoài.
4. **Rule hoặc luật:** đầu vào đúng nhưng rule engine ra trạng thái hay mã sai.
5. **Nhãn đáng tranh luận:** người xem lại thấy nhãn có thể sai.

Nhóm 5: **không** đổi nhãn, không loại câu. Ghi riêng trong báo cáo: "nếu nhãn câu X sai thì kết quả thành …", kèm số chính thức theo nhãn đã khoá.

## 7. Những gì đã biết trước về bộ này (nêu trong báo cáo)
- 12 câu, đều từ code thật của 5 repo công khai chưa dùng, ẩn danh.
- 4 câu C3 có giả định loại hình và quy mô ghi nguyên văn trong `mo_ta` (không lấy từ repo); 8 câu còn lại không biết loại hình nên C3 là `CAN_NGUOI_XAC_NHAN`.
- C1 có đủ 3 trạng thái nhưng chỉ 1 câu `CAN_LUAT_SU`; chỉ 1 câu tag `vt`: không kết luận gì từ riêng hai chỗ này.
- 3 câu không có bảng CSDL nên `schema` rỗng (ngoại lệ ở `data/cases/LABELING.md` §14).
- Khoa đã xem nhãn bộ mù trước khi làm phần cơ học của #24 (ghi ở `spec.md` §10); Minh, người sửa prompt, không xem.

## 8. Sau khi có kết quả
- Không sửa prompt, từ khoá, rule theo kết quả này trước CP4.
- Sửa sau CP4 thì ghi riêng trong `spec.md` §10 là "sửa sau khi xem bộ mù"; từ đó bộ này là dữ liệu dev, không còn gọi là mù.
