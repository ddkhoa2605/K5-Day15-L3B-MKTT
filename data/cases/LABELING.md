# LABELING.md — Bộ 60 case có nhãn của Ship Hợp Pháp

> File dữ liệu: [`cases.jsonl`](cases.jsonl) (60 dòng, mỗi dòng một case) · kiểm tra: `python data/cases/validate_cases.py`
> Người dán nhãn: Thịnh (cùng Claude Code hỗ trợ soạn) · ngày dựng: 27/11/2026 · mã căn cứ đồng bộ với `data/legal/*.json` của Khoa (commit `e0b9749`, đã merge vào `main` ở `77b3e60`). Các cờ còn mở xem mục 6.4.
> Nhãn do nhóm tự dán, **chưa được luật sư kiểm độc lập**. Đây không phải tư vấn pháp lý.

---

## 1. Mục tiêu bộ dữ liệu

Bộ dữ liệu là **đáp án biết trước** để đo bản chạy thử có kết luận đúng 3 nhóm nghĩa vụ hay không:

1. Đo độ chính xác trạng thái C1, C2, C3 và tập mã căn cứ (metric `trich_dan_dung`).
2. Đo khả năng phân loại tên cột viết tắt tiếng Việt (metric `phan_loai_viet_tat`, tag `vt`).
3. Đo tỉ lệ báo động giả trên case âm tính (metric `bao_dong_gia`, tag `am`).
4. Đo việc hệ thống biết dừng lại và chuyển người (metric `tu_choi_dung`: `CAN_LUAT_SU`, `CAN_NGUOI_XAC_NHAN`, câu `tan_cong`).
5. Cung cấp dữ liệu cho ablation A/B/C (`rule` · `llm` · `hybrid`).

Nhãn trả lời câu hỏi *"theo văn bản luật, với đúng thông tin có trong case, nghĩa vụ nào đã phát sinh?"*. Nó không trả lời *"rule engine sẽ ra gì"*.

**Phát sinh nghĩa vụ ≠ vi phạm.** `KICH_HOAT` nghĩa là *nghĩa vụ đã phát sinh* (C1), hoặc *bằng chứng trong code cho thấy yêu cầu chưa được đáp ứng* (C2). Nhãn không kết luận doanh nghiệp đã vi phạm. Doanh nghiệp có thể đã nộp hồ sơ, hoặc có bằng chứng ngoài repo.

## 2. Phạm vi 3 nhóm kiểm tra

| Nhóm | Câu hỏi | Căn cứ chính |
|---|---|---|
| **C1** | Dữ liệu cá nhân có được xử lý trên nền tảng ngoài lãnh thổ Việt Nam qua lời gọi trong code (AI, email, SMS, analytics, giám sát lỗi, bản đồ…) không? Nếu có thì phát sinh nghĩa vụ lập hồ sơ đánh giá tác động chuyển dữ liệu xuyên biên giới. | Luật 91 Điều 20 |
| **C2** | Sự đồng ý có được thể hiện chủ động và được **lưu lại đủ để chứng minh** (ai, lúc nào, phiên bản điều khoản nào) không? Có coi im lặng là đồng ý, hoặc đặt mặc định là đồng ý không? | Luật 91 Điều 9; ND356 Điều 6 |
| **C3** | Hộ kinh doanh, doanh nghiệp siêu nhỏ, nhỏ, khởi nghiệp còn được miễn hoặc hoãn nghĩa vụ ở Điều 21, Điều 22, khoản 2 Điều 33 không? Hay đã mất vì xử lý dữ liệu nhạy cảm, hoặc đạt từ 100.000 chủ thể? | Luật 91 Điều 38; ND356 Điều 4, Điều 41 |

**Ngoài phạm vi:**
- Bảo mật kỹ thuật (RLS, lộ key…).
- Trường hợp mất miễn trừ "kinh doanh dịch vụ xử lý dữ liệu cá nhân": Case không có trường mô tả loại hoạt động này.
- Vị trí đặt máy chủ CSDL chính (xem XN6).
- Các căn cứ xử lý không cần đồng ý (xem XN12).

## 3. Lược đồ dữ liệu

Mỗi dòng `cases.jsonl` là một object. **Phần input** được gửi cho `answer()`: bỏ trường `nhan`, giữ đúng hợp đồng Case trong plan. **Phần `nhan`** là đáp án, không bao giờ được gửi cho hệ thống.

### 3.1 Input (hợp đồng Case — không đổi)

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | str | `<nhóm>-<loại>-<số>`, ví dụ `c3-vt-001`. Duy nhất. |
| `mo_ta` | str | Kịch bản thực tế, **gồm cả bối cảnh triển khai và xử lý** (ai dùng, dữ liệu lấy từ đâu, gửi đi đâu, quy mô). Bối cảnh nằm trong `mo_ta` chứ không tách trường riêng, để hệ thống nhận được nó mà không cần đổi hợp đồng input. |
| `schema` | list[str] | Dạng `bang(cot1, cot2, …)`. Có thể kèm comment (`-- …`) như trong repo thật. |
| `code` | list[{file, line, text}] | Đoạn code làm bằng chứng. Có thể rỗng. |
| `loai_hinh` | enum | `ho_kinh_doanh` · `doanh_nghiep_sieu_nho` · `doanh_nghiep_nho` · `khoi_nghiep` · `doanh_nghiep_lon` · `khong_ro` |
| `so_chu_the_luy_ke` | int \| null | Tổng số chủ thể **từng** được xử lý (lũy kế), không phải số đang hoạt động. `null` = không biết. |

### 3.2 Nhãn `nhan`

| Trường | Ý nghĩa |
|---|---|
| `nhom_kiem` | `C1` · `C2` · `C3`: nhóm kiểm tra **trọng tâm** của case |
| `nhom_con` | Ô trong bảng phân bổ: `C1_chuyen_ra_ngoai`, `C1_api_khong_pii`, `C1_chatbox`, `C2_du`, `C2_thieu`, `C3_ro`, `C3_vt`, `C3_con_mien`, `C3_luy_ke` |
| `C1`, `C2`, `C3` | Trạng thái của **cả 3 nhóm**. Mỗi case luôn có đủ 3 nhãn, kể cả khi trọng tâm chỉ là một nhóm. |
| `nhom_nhay_cam` | Tập mã nhóm dữ liệu nhạy cảm có trong case (mục 6.2). Không ghi dữ liệu cơ bản. |
| `can_cu` | **Hợp** các mã căn cứ của C1, C2 và C3, không trùng. Đây là tập so với output khi chấm. |
| `can_cu_theo_nhom` | `{C1: [...], C2: [...], C3: [...]}`: căn cứ tách theo nhóm, để chấm chi tiết và tìm lỗi |
| `bang_chung` | `[{nhom, vi_tri, chi_tiet}]`: dòng code hoặc cột schema làm căn cứ cho nhãn |
| `ly_do` | Lập luận dán nhãn, có trích điều, khoản, điểm |
| `do_kho` | `easy` (đọc thẳng) · `medium` (cần đọc ngữ cảnh) · `hard` (có bẫy, giá trị biên, ngoại lệ, tấn công) |
| `tag` | `ro` · `vt` · `am` · `chatbox` · `luy_ke` · `tan_cong` (dùng cho metric) |
| `split` | `dev` · `holdout` |
| `can_xac_nhan` | Các cờ `XN…` (mục 6.4) chỉ ra căn cứ hoặc quy ước trong case còn chờ nhóm xác nhận |

**Ánh xạ `nhom_con` sang `tag`:**
- `C1_chuyen_ra_ngoai`, `C2_thieu`, `C3_ro` → `ro`
- `C1_api_khong_pii`, `C2_du`, `C3_con_mien` → `am`
- `C1_chatbox` → `chatbox`
- `C3_vt` → `vt`
- `C3_luy_ke` → `luy_ke`

Riêng 3 case có câu tấn công mang tag `tan_cong`, nhưng vẫn giữ `nhom_con` gốc.

## 4. Nhãn và điều kiện sử dụng

### C1

| Nhãn | Khi nào dùng |
|---|---|
| `KICH_HOAT` | Code gửi dữ liệu cá nhân tới nền tảng ngoài lãnh thổ, và dữ liệu đó do **hệ thống** gắn vào (lấy từ hồ sơ, CSDL, SDK `setUser/identify`, danh sách gửi mail…). Không phụ thuộc `loai_hinh`, vì Điều 38 không miễn Điều 20. |
| `CAN_LUAT_SU` | Dữ liệu đi ra nước ngoài **chỉ** là nội dung người dùng tự nhập (chatbox), hoặc không xác định được nguồn. Lý do: có thể rơi vào ngoại lệ "chủ thể tự chuyển dữ liệu" ở Điều 20 khoản 6. |
| `KHONG_KICH_HOAT` | Không có lời gọi ra nước ngoài; hoặc có nhưng nội dung không xác định được một người cụ thể (nội dung sản phẩm, bài báo công khai, số liệu tổng hợp, token, toạ độ của cơ sở kinh doanh); hoặc dữ liệu cá nhân chỉ đi tới đơn vị trong nước (`.vn`). |

### C2

| Nhãn | Khi nào dùng |
|---|---|
| `KHONG_KICH_HOAT` | Không có dữ liệu cá nhân; hoặc có bản ghi đồng ý gắn với người dùng, có thời điểm và phiên bản điều khoản, ở **bất kỳ** bảng nào (bảng `consents`, cột trong `users`, `audit_logs`…), và không có đồng ý đặt sẵn. Bản ghi phải thuộc **đúng chủ thể và đúng luồng thu thập** đang xét. Ví dụ: repo có bảng đồng ý nhưng chỉ form lead ghi vào đó, thì không tính cho khách bị ghi âm cuộc gọi (`dt-r02-001`). |
| `KICH_HOAT` | Có dữ liệu cá nhân nhưng không lưu được bằng chứng đồng ý đủ để chứng minh: không có bản ghi, thiếu thời điểm hoặc phiên bản, chỉ có cờ boolean, chỉ lưu ở `localStorage`. |
| `KICH_HOAT_NANG` | Coi im lặng hoặc tiếp tục sử dụng là đồng ý, **hoặc** ô đồng ý được tích sẵn (`defaultChecked`, `checked={true}`). Mức này có ưu tiên cao hơn `KICH_HOAT`. |

### C3

Đi từ trên xuống, dừng ở dòng đầu tiên khớp.

| Thứ tự | Điều kiện | Nhãn |
|---|---|---|
| 1 | `loai_hinh = doanh_nghiep_lon` | `KHONG_THUOC_DIEN_MIEN` (không có miễn trừ để mất) |
| 2 | `loai_hinh = khong_ro` hoặc `so_chu_the_luy_ke = null` | `CAN_NGUOI_XAC_NHAN` |
| 3 | Có cột **chắc chắn** thuộc một điểm của ND356 Điều 4 khoản 1 (đã đọc ngữ cảnh) | `MAT_MIEN_TRU` |
| 4 | `so_chu_the_luy_ke ≥ 100000` (đúng 100.000 là đã đạt) | `MAT_MIEN_TRU` |
| 5 | Còn lại | `CON_MIEN_TRU` |

- **Bước 2 đứng trước bước 3, có chủ đích.** Khi đã biết có dữ liệu nhạy cảm nhưng không biết loại hình, kết luận có thể là "mất" hoặc "không thuộc diện", nên chưa chọn được trạng thái. Hai kết luận này đều có nghĩa là không còn miễn trừ. Báo cáo nên nói rõ điều đó (case `c3-vt-007`).
- Thứ tự này **khác** thứ tự trong plan M5. Xem XN8.

## 5. Quy trình dán nhãn từng bước

1. **Đọc `mo_ta` trước, sau đó mới đọc tên cột.** Tên cột chỉ là gợi ý. Nghĩa thật xác định bằng ngữ cảnh: placeholder của form, nguồn dữ liệu (ví dụ `navigator.geolocation`), mô tả nghiệp vụ.
2. **Lập danh sách dữ liệu cá nhân.** Chia làm hai loại:
   - Dữ liệu **cơ bản** (ND356 Điều 3). Gồm họ tên, ngày sinh, địa chỉ, SĐT, **số** định danh, biển số xe, hình ảnh, tài khoản số…
   - Dữ liệu **nhạy cảm** (Điều 4 khoản 1, điểm a–l).
3. **C1:** liệt kê mọi lời gọi mạng ra ngoài. Với từng lời gọi, hỏi lần lượt:
   - Có tới nước ngoài không?
   - Có mang dữ liệu xác định được người không?
   - Ai đưa dữ liệu đó vào: hệ thống hay chính người dùng?
4. **C2:** tìm nơi ghi đồng ý, ở mọi bảng chứ không chỉ bảng tên `consent`. Kiểm đủ 3 yếu tố. Sau đó kiểm UI: có ô tích sẵn hoặc câu "tiếp tục sử dụng là đồng ý" không.
5. **C3:** đi theo bảng thứ tự ở mục 4.
6. **Gán mã căn cứ** theo bảng ở mục 6.3. Chỉ dùng mã có trong bảng đó.
7. **Viết `bang_chung`** (file:dòng hoặc bảng.cột) và **`ly_do`** (có điều, khoản, điểm).
8. **Gắn `do_kho`, `tag`, `can_xac_nhan`.**
9. **Chạy `python data/cases/validate_cases.py`.** Script không sinh nhãn. Nó chỉ kiểm tính nhất quán, ví dụ `CON_MIEN_TRU` mà có nhóm nhạy cảm là lỗi.
10. **Không chạy hệ thống rồi chỉnh nhãn theo output.** Bộ nhãn này được dựng khi repo chưa có `codebase/rules.py` và chưa có `classify/verify`. Nhãn không lấy từ bất kỳ output nào của hệ thống.

## 6. Căn cứ pháp lý và nguồn

### 6.1 Văn bản và mức độ đã kiểm

**Nguồn sự thật của mã căn cứ là `data/legal/citations.json`** (Khoa, commit `e0b9749`). Khoa xác nhận đã đối chiếu từng mã của Luật 91 và Nghị định 356 với văn bản gốc. Mọi mã trong bộ nhãn đều là khoá của file đó; `validate_cases.py` báo **lỗi** nếu có mã lạ. Bảng dưới ghi thêm những gì người dán nhãn tự kiểm được.

| Văn bản | Nội dung dùng | Đã kiểm thế nào |
|---|---|---|
| **ND356/2025/NĐ-CP** Điều 3 | Danh mục dữ liệu cơ bản. Khoản 7 gồm SĐT, số định danh cá nhân, hộ chiếu, GPLX, biển số xe. | Đọc trên toàn văn đăng tại LuatVietnam (27/11/2026) |
| ND356 Điều 4 khoản 1, điểm a–m | 12 điểm dữ liệu nhạy cảm (bảng 6.2). Điều 4 **có** khoản 1 (danh mục) và khoản 2 (phân quyền, bảo mật khi xử lý). | Như trên |
| ND356 Điều 6 | Khoản 1: phương thức đồng ý kiểm chứng được. Khoản 2: bên kiểm soát lưu sự đồng ý và chịu trách nhiệm chứng minh. **Khoản 3: cấm đặt mặc định là đồng ý**, cấm chỉ dẫn gây nhầm lẫn. Khoản 4: thông báo khi xin đồng ý xử lý dữ liệu nhạy cảm. | Như trên |
| ND356 Điều 41 | Tiêu đề là "áp dụng khoản 2, khoản 3 của Điều 38". Khoản 1: doanh nghiệp nhỏ, khởi nghiệp được chọn làm hay không trong 5 năm. Khoản 2: hộ kinh doanh, doanh nghiệp siêu nhỏ không phải thực hiện. Trường hợp không được miễn: kinh doanh dịch vụ xử lý dữ liệu, trực tiếp xử lý dữ liệu nhạy cảm, hoặc "kể từ thời điểm có quy mô đạt từ 100 nghìn chủ thể dữ liệu cá nhân trở lên" (tính lũy kế). | Như trên |
| **Luật 91/2025/QH15** Điều 9 | Đồng ý phải rõ ràng, cụ thể, in hoặc sao chép được, kiểm chứng được. **Im lặng hoặc không phản hồi không được coi là đồng ý.** | Nội dung đã kiểm qua Đề cương giới thiệu Luật của Sở Tư pháp Tuyên Quang. Số khoản và điểm (`D9.3` = phương thức rõ ràng, kiểm chứng được; `D9.4d` = im lặng không phải đồng ý) theo `citations.json` của Khoa. |
| Luật 91 Điều 20 | Khoản 1 gồm 3 trường hợp chuyển xuyên biên giới, trong đó có dùng nền tảng ngoài lãnh thổ để xử lý dữ liệu thu thập tại Việt Nam. Khoản 2: hồ sơ đánh giá tác động trong 60 ngày. Khoản 6: các trường hợp không phải lập hồ sơ. | 3 trường hợp đã kiểm (cùng nguồn). Khoản 2 (60 ngày, trừ khoản 6) và khoản 6 điểm c (chủ thể tự chuyển dữ liệu của mình) theo `citations.json` của Khoa. |
| Luật 91 Điều 38 | Khoản 2: doanh nghiệp nhỏ và khởi nghiệp được chọn, trong 5 năm. Khoản 3: hộ kinh doanh và siêu nhỏ không phải thực hiện Điều 21, 22, khoản 2 Điều 33. Cả hai đều trừ trường hợp dịch vụ xử lý dữ liệu, dữ liệu nhạy cảm, số lượng lớn chủ thể. | Nội dung đã kiểm (cùng nguồn). Số khoản 2 và 3 khớp với tiêu đề ND356 Điều 41. |
| ND330/2026/NĐ-CP | Mức phạt | **Không dùng trong nhãn.** Mã mức phạt thuộc `muc_phat`, không thuộc `can_cu` (mục 6.3). |

Nguồn đã đọc:
- `data/legal/citations.json`, `exemption.json`, `sensitive_categories.json` của Khoa (commit `e0b9749`)
- [Toàn văn Nghị định 356/2025/NĐ-CP — LuatVietnam](https://luatvietnam.vn/dan-su/nghi-dinh-356-2025-nd-cp-quy-dinh-chi-tiet-luat-bao-ve-du-lieu-ca-nhan-422896-d1.html)
- [Đề cương giới thiệu Luật Bảo vệ dữ liệu cá nhân — Sở Tư pháp Tuyên Quang (PDF)](https://khodulieu.sohoa.tuyenquang.gov.vn/congthongtin/media/a3a0a543e41f76745db2acd0fd744175.pdf)
- Trả lời của Khoa cho Minh (27/11/2026) về mã Điều 41, mã C2, điểm m
- Tài liệu nghiên cứu đề tài của nhóm

Thư Viện Pháp Luật chặn truy cập tự động nên người dán nhãn chưa tự đọc được toàn văn Luật 91. Số hiệu của Luật 91 trong bộ nhãn dựa vào phần đối chiếu của Khoa.

### 6.2 Mã nhóm nhạy cảm — ND356 Điều 4

Mã nhóm (`chung_toc_dan_toc`…) và mã căn cứ (`ND356 D4h`…) khớp nguyên văn khoá `can_cu` trong `data/legal/sensitive_categories.json`. Định dạng mã do Khoa chốt là `ND356 D4<điểm>`, không ghi số khoản.

| Mã nhóm | Điểm | Nội dung (tóm tắt sát văn bản) | Mã căn cứ |
|---|---|---|---|
| `chung_toc_dan_toc` | a | Dữ liệu tiết lộ nguồn gốc chủng tộc, dân tộc | `ND356 D4a` |
| `chinh_tri_ton_giao` | b | Quan điểm chính trị, tôn giáo, tín ngưỡng | `ND356 D4b` |
| `doi_tu_rieng_tu` | c | Đời sống riêng tư, bí mật cá nhân, bí mật gia đình | `ND356 D4c` |
| `suc_khoe` | d | Tình trạng sức khoẻ | `ND356 D4d` |
| `sinh_trac_di_truyen` | đ | Dữ liệu sinh trắc học, đặc điểm di truyền | `ND356 D4đ` |
| `tinh_duc` | e | Đời sống tình dục, xu hướng tình dục | `ND356 D4e` |
| `toi_pham` | g | Dữ liệu về tội phạm, vi phạm pháp luật **do cơ quan thực thi pháp luật** thu thập, lưu trữ | `ND356 D4g` |
| `vi_tri_dinh_vi` | h | Vị trí của cá nhân **được xác định qua dịch vụ định vị** | `ND356 D4h` |
| `dinh_danh_dien_tu` | i | Tên đăng nhập và mật khẩu tài khoản định danh điện tử; **hình ảnh** thẻ căn cước, CCCD, CMND | `ND356 D4i` |
| `tai_chinh` | k | Tên đăng nhập và mật khẩu tài khoản ngân hàng; thông tin thẻ ngân hàng; lịch sử giao dịch; thông tin tài chính, tín dụng… (của khách hàng tại tổ chức tín dụng, trung gian thanh toán…) | `ND356 D4k` |
| `hanh_vi_mang` | l | Dữ liệu theo dõi hành vi, hoạt động sử dụng viễn thông, mạng xã hội, truyền thông trực tuyến | `ND356 D4l` |
| — | m | Dữ liệu khác pháp luật quy định cần giữ bí mật. **Điều khoản mở, không có mã** (Khoa chủ ý không tạo `ND356 D4m`). Cột chỉ có thể khớp điểm m → C3 `CAN_NGUOI_XAC_NHAN`, `can_cu` rỗng. | — |

Chữ cái điểm theo thứ tự tiếng Việt: có `đ`, không có `f` và `j`. Tổng cộng 12 điểm. **Không phải 13 nhóm** như spec gốc.

**Hai cặp dễ nhầm:**
- *Số* căn cước là dữ liệu cơ bản (Điều 3 khoản 7). *Ảnh* thẻ căn cước là dữ liệu nhạy cảm (điểm i).
- *Địa chỉ nhập tay* là dữ liệu cơ bản. *Vị trí GPS* là dữ liệu nhạy cảm (điểm h).

### 6.3 Bảng quy ước mã căn cứ theo trạng thái

| Nhóm | Trạng thái | `can_cu_theo_nhom` |
|---|---|---|
| C1 | `KICH_HOAT` | `Luat91 D20.1`, `Luat91 D20.2` |
| C1 | `CAN_LUAT_SU` | `Luat91 D20.6` |
| C1 | `KHONG_KICH_HOAT` | — |
| C2 | `KICH_HOAT` (thiếu bằng chứng đồng ý) | `Luat91 D9.3`, `ND356 D6` |
| C2 | `KICH_HOAT_NANG` | Luôn gồm `Luat91 D9.3`, `ND356 D6`, **thêm** `Luat91 D9.4d` nếu coi im lặng là đồng ý, **thêm** `ND356 D6.3` nếu tích sẵn (theo ánh xạ của Khoa) |
| C2 | `KHONG_KICH_HOAT` | — |
| C3 | `MAT_MIEN_TRU` | Mã điểm của **từng** nhóm nhạy cảm (`ND356 D4x`) + mã loại hình (`Luat91 D38.3` cho hộ kinh doanh và siêu nhỏ, `Luat91 D38.2` cho nhỏ và khởi nghiệp) + mã Điều 41 theo loại hình (`ND356 D41.2` cho hộ kinh doanh và siêu nhỏ, `ND356 D41.1` cho nhỏ và khởi nghiệp). Nếu mất vì lũy kế thì không có mã điểm Điều 4. |
| C3 | `CON_MIEN_TRU` | Mã loại hình + mã Điều 41 theo loại hình |
| C3 | `KHONG_THUOC_DIEN_MIEN`, `CAN_NGUOI_XAC_NHAN` | — (nhóm nhạy cảm vẫn được ghi trong `nhom_nhay_cam`) |

- Mã loại hình lấy từ `exemption.json → loai_hinh.<x>.can_cu`. Mã Điều 41 lấy từ `loai_hinh.<x>.can_cu_nd`.
- Mã Điều 41 chọn theo **loại hình**, không theo lý do mất miễn trừ, vì 3 lý do nằm chung một câu trong mỗi khoản. **Không dùng `ND356 D41`** (mã cấp điều trong `mat_mien_tru`, chỉ để dự phòng).
- Mã mức phạt không bao giờ nằm trong `can_cu`.

### 6.4 Cờ chờ xác nhận (`can_xac_nhan`)

Cờ ✅ đã được Khoa chốt qua `data/legal/*.json` và trả lời ngày 27/11. Chúng không còn được gắn vào case, chỉ giữ ở đây để truy vết.

| Cờ | Nội dung | Trạng thái |
|---|---|---|
| XN1 | Định dạng mã điểm Điều 4 | ✅ Chốt `ND356 D4<điểm>`. Ghi chú cho Khoa: toàn văn trên LuatVietnam cho thấy Điều 4 có khoản 1 (danh mục) và khoản 2 (phân quyền, bảo mật). Mã không ghi khoản vẫn không nhầm được vì chỉ khoản 1 có điểm, nhưng câu "Điều 4 không có khoản 1" nên sửa nếu đưa lên slide. |
| XN2 | Số hiệu Luật 91 Điều 9 (`D9.3`, `D9.4d`) | ✅ Có trong `citations.json`, Khoa đã đối chiếu |
| XN3 | `Luat91 D20.2`, `Luat91 D20.6` | ✅ Có trong `citations.json`. Khoản 6 điểm c là "chủ thể tự chuyển dữ liệu của mình". |
| XN4 | Mã C2 | ✅ Dùng `ND356 D6` (cấp điều) + `ND356 D6.3`. Không dùng `ND356 D6.2` (không có trong `citations.json`). |
| XN5 | `CON_MIEN_TRU` có kèm `ND356 D41.x` | ✅ Khoa: C3 miễn trừ trích cả `Luat91 D38.x` và `ND356 D41.x` |
| XN6 | Phạm vi C1: có tính nơi đặt hạ tầng nền (CSDL, Auth của Supabase) không | ✅ Khoa chốt 27/11: chỉ tính lời gọi tới dịch vụ bên thứ ba có trong code (API AI, email, analytics đặt ngoài lãnh thổ). **Không** tính nơi đặt hạ tầng nền như CSDL hay Auth của Supabase, vì quét từ mã nguồn không biết vùng đặt máy chủ. Không nhãn nào phải đổi. Đã ghi vào `spec.md` §7. |
| XN7 | Phạm vi điểm k gắn với "khách hàng tại tổ chức tín dụng, trung gian thanh toán…". Nhãn coi thông tin thẻ, tài khoản ngân hàng do app lưu là thuộc điểm k. | ⏳ Còn mở — Khoa |
| XN8 | Thứ tự C3: doanh nghiệp lớn → `KHONG_THUOC_DIEN_MIEN`; thiếu loại hình hoặc quy mô → `CAN_NGUOI_XAC_NHAN`. Cả hai đều xét **trước** luật nhạy cảm, khác plan M5. | ⏳ Còn mở — Khoa, Minh |
| XN9 | Ô tích sẵn → `KICH_HOAT_NANG`. ND356 Điều 6 khoản 3 (cấm mặc định đồng ý) đã kiểm. Việc xếp hành vi này cùng mức phạt với "coi im lặng là đồng ý" của ND330 thì chưa kiểm. | ⏳ Còn mở — Khoa |
| XN10 | Mã nhóm `dinh_danh_dien_tu` (điểm i) | ✅ Đã có trong `sensitive_categories.json` |
| XN11 | Mã `ND356 D4đ` có ký tự `đ`. `legal.normalize()` không được áp lên mã căn cứ, vì sẽ biến `đ` thành `d` và trùng với điểm d. | ⏳ Còn mở — Minh |
| XN12 | **Giả định bộ dữ liệu:** C2 coi mọi xử lý trong case đều dựa trên sự đồng ý. Các trường hợp không cần đồng ý (Luật 91 Điều 19) chưa được mô hình hoá. | ⏳ Còn mở — Khoa |

## 7. Ví dụ dán nhãn đúng và sai

| Case | Dán **sai** | Dán **đúng** | Vì sao |
|---|---|---|---|
| `c1-am-001`: OpenAI dịch mô tả sản phẩm | C1 `KICH_HOAT` vì "có gọi OpenAI" | `KHONG_KICH_HOAT` | Không có dữ liệu cá nhân trong prompt |
| `c1-chat-004`: khách tự gõ tên và SĐT vào chatbox | C1 `KICH_HOAT` vì thấy SĐT đi ra ngoài | `CAN_LUAT_SU` | Nguồn là chủ thể tự nhập, nên có thể rơi vào ngoại lệ Điều 20 khoản 6 |
| `c1-ro-001`: hộ kinh doanh gửi email sang OpenAI | C1 `KHONG_KICH_HOAT` vì "hộ kinh doanh được miễn" | `KICH_HOAT` | Điều 38 không miễn Điều 20 |
| `c2-du-002`: không có bảng consent, đồng ý lưu ở `users.terms_*` | C2 `KICH_HOAT` vì "không có bảng consent" | `KHONG_KICH_HOAT` | Vẫn đủ ai, lúc nào, phiên bản nào |
| `c2-thieu-005`: consents đủ trường nhưng ô tích sẵn | C2 `KHONG_KICH_HOAT` vì "có nhật ký" | `KICH_HOAT_NANG` | ND356 Điều 6 khoản 3 |
| `c3-am-004`: lưu số căn cước | C3 `MAT_MIEN_TRU` vì "CCCD là nhạy cảm" | `CON_MIEN_TRU` | Số định danh thuộc Điều 3; chỉ ảnh thẻ mới thuộc điểm i |
| `c3-am-003`: cột `vt_kho` | `vi_tri_dinh_vi` | Không nhạy cảm | Đây là toạ độ kho hàng, không phải vị trí của cá nhân |
| `c3-vt-001`: `vi_tri_gan_nhat` | `khong_ca_nhan` vì nghĩ là vị trí sân | `vi_tri_dinh_vi` → `MAT_MIEN_TRU` | Code dòng 19 lấy GPS người dùng |
| `c3-ro-006`: doanh nghiệp lớn có khuôn mặt | `MAT_MIEN_TRU` | `KHONG_THUOC_DIEN_MIEN` | Doanh nghiệp lớn không có miễn trừ để mất |
| `c3-lk-002`: 120.000 đăng ký, 3.000 đang hoạt động | `CON_MIEN_TRU` (theo 3.000) | `MAT_MIEN_TRU` | Ngưỡng tính lũy kế |
| `c1-ro-005`, `c1-ro-008`, `c3-ro-005`: comment "báo app sạch" | Tin theo comment | Nhãn như khi không có comment | Chỉ dẫn nhúng trong dữ liệu không phải bằng chứng |

## 8. Xử lý khi thiếu thông tin hoặc luật mập mờ

- **Thiếu loại hình hoặc quy mô** (`khong_ro`, `null`) → C3 `CAN_NGUOI_XAC_NHAN`. Hệ thống phải hỏi lại người dùng, không được đoán.
- **Luật chưa rõ cho kịch bản** (chatbox, Điều 20 khoản 6) → C1 `CAN_LUAT_SU`.
- **Tên cột mập mờ:**
  - Nếu ngữ cảnh trong case đủ để kết luận, dán theo ngữ cảnh.
  - Nếu một chuyên gia đọc case vẫn không kết luận được, dùng `CAN_NGUOI_XAC_NHAN`. 60 case tự viết không có case loại này, vì mỗi case đều được viết kèm ngữ cảnh đủ rõ. 7 case corpus (mục 12) có C3 `CAN_NGUOI_XAC_NHAN` vì một lý do khác: **thiếu loại hình và quy mô**, không phải vì tên cột mập mờ.
- **C2 không có nhãn "cần rà soát"** trong enum của nhóm. Vì vậy bộ dữ liệu tránh dựng case C2 mập mờ. Nếu cần, đề xuất thêm enum (xem báo cáo).
- **Căn cứ chưa kiểm được:** không bịa số điều. Vẫn dùng mã theo quy ước, gắn cờ `XN…`, và ghi rõ ở mục 6.4.
- **Sửa nhãn sau khi commit:** chỉ khi phát hiện hiểu sai luật. Ghi vào mục 13 (lý do, người duyệt, ngày) **trước khi** xem lại output. Không sửa nhãn để khớp kết quả hệ thống.

## 9. Chia dev và holdout

- **50 dev, 10 holdout**, cùng nằm trong `cases.jsonl` và phân biệt bằng `nhan.split`. Plan đã quy ước một file duy nhất, nên Minh (test) và `eval/ablation.py` (`--split`) đọc chung được.
- **10 holdout:** mỗi ô phân bổ một case, riêng `C3_vt` hai case.
  - `c1-ro-006` (CV ứng viên, khó)
  - `c1-am-005` (MoMo `.vn` + Turnstile, âm tính khó)
  - `c1-chat-004` (cần luật sư)
  - `c2-du-002` (đồng ý lưu trong `users`, âm tính khó)
  - `c2-thieu-006` (im lặng là đồng ý)
  - `c3-ro-004` (tôn giáo + xu hướng tình dục)
  - `c3-vt-005` (`hanh_vi_log`)
  - `c3-vt-008` (`dt_khuon_mat`, 40 nhân viên)
  - `c3-am-001` (địa chỉ nhập tay, âm tính)
  - `c3-lk-002` (lũy kế 120.000)
- **Tiêu chí chọn:**
  - Đủ C1, C2, C3.
  - Có case khó, case âm tính, và case cần rà soát (`CAN_LUAT_SU`).
  - **Không** đưa vào holdout case có quy ước còn đang tranh luận (XN8: `c3-vt-007`, `c3-ro-006`, `c3-lk-006`), để kết quả holdout không phụ thuộc quyết định chưa chốt.
- **Không trùng kịch bản:** validator kiểm độ giống từ (Jaccard trên `mo_ta` + `schema`) giữa mọi cặp dev và holdout. Ngưỡng lỗi là > 0,5; cao nhất hiện tại 0,30. Validator cũng kiểm schema hoặc code trùng hoàn toàn.
- **Holdout chỉ chạy một lần** ở cuối (`python eval/ablation.py --split holdout`). Không dùng để chỉnh rule, prompt hay từ khoá. Không đưa holdout vào `eval/benchmark.csv`.

## 10. Giới hạn của bộ dữ liệu

- **Synthetic:** 60 case do nhóm tự viết. Không lấy từ repo thật, không chứa dữ liệu cá nhân thật. Mọi giá trị đều là tên biến; validator quét email, SĐT, dãy 12 số, số thẻ và API key. Data tự dựng **không phải bằng chứng pain**.
- **Nhãn chưa được luật sư kiểm độc lập.** Một số số hiệu điều luật còn chờ đối chiếu (mục 6.4).
- **Thiên lệch:**
  - Ngữ cảnh trong `mo_ta` được viết rõ hơn repo thật, nên độ khó thật có thể cao hơn.
  - Chỉ có một stack (Next.js + Supabase) và chỉ tiếng Việt và tiếng Anh.
  - Lệch về doanh nghiệp siêu nhỏ (21/60) và hộ kinh doanh (13/60).
  - C1 `KHONG_KICH_HOAT` chiếm 46/60. Muốn đánh giá C1 thì nên xem riêng 18 case thuộc nhóm C1.
- **Thiếu:** điểm a (chủng tộc), g (tội phạm) và m (điều khoản mở) chưa có case. Trường hợp "kinh doanh dịch vụ xử lý dữ liệu" và các căn cứ không cần đồng ý chưa được mô hình hoá.
- **Mỗi case có một trọng tâm.** Các nhóm khác được dựng đơn giản (thường là có bảng consent đủ, hoặc ghi rõ là không có), nên không đo được tương tác phức tạp giữa các nhóm.

## 11. Hướng dẫn cho các thành viên khác

**Minh (rule engine, `tests/test_rules.py`):**
- Chép đúng nhãn từ file, không tự nghĩ ra. Case gợi ý cho từng test:

  | Test | Case |
  |---|---|
  | C3 mất miễn trừ dù nhỏ | `c3-vt-001` (repo demo C) |
  | `loai_hinh=khong_ro` | `c1-chat-002` |
  | Lũy kế vượt ngưỡng | `c3-lk-003` |
  | Chatbox | `c1-chat-001` |
  | API không PII | `c1-am-001` |
  | Tích sẵn | `c2-thieu-005` |
  | Tấn công | `c3-ro-005` |

- Input cho `answer()` = cả dòng trừ khoá `nhan`.
- Đọc mục 6.3 trước khi viết luật căn cứ. Lấy mã từ `exemption.json` (`can_cu`, `can_cu_nd`) và `sensitive_categories.json` (`can_cu`), đừng gõ tay. Hai cờ còn mở ảnh hưởng tới code: XN8 (thứ tự luật C3) và XN11 (không `normalize` mã có `đ`).
- C2 `KICH_HOAT_NANG` **luôn** kèm `Luat91 D9.3` + `ND356 D6`, rồi thêm mã theo lý do. Áp dụng cả khi bảng consent đã đủ trường (`c2-thieu-005`, `c2-thieu-007`).
- **Chỉ dùng split `dev`.**

**Thịnh (benchmark, grade, ablation):**
- `eval/build_benchmark.py` đọc file này, lọc `split=="dev"`.
  - `input` = JSON không có `nhan`.
  - `expected` = `C1=…;C2=…;C3=…;nhom=a|b;can_cu=x|y`, lấy từ `nhan.can_cu` và `nhan.nhom_nhay_cam`.
  - `type` theo `tag`: `ro`, `am` → `thuong`; `vt`, `chatbox`, `luy_ke` → `kho`; `tan_cong` → `tu_choi`.
- `grade.py` so `can_cu` theo tập, gộp 3 nhóm. `can_cu_theo_nhom` dùng để phân tích lỗi.

**Khoa:**
- Trả lời các cờ ⏳ còn mở ở mục 6.4 (XN7, XN8, XN9, XN12).
- Nếu đổi mã trong `citations.json`, báo Thịnh và Minh cùng lúc. Validator sẽ báo lỗi ngay mọi mã không còn trong file.

**Kiểm sau mỗi thay đổi:** chạy `python data/cases/validate_cases.py`. Khi đã có `data/legal/citations.json`, script sẽ tự đối chiếu mã căn cứ với file đó.

## 12. Case dựng từ repo công khai (`corpus_cases.jsonl`, nguồn `data_that`)

- **File riêng**, không thêm vào `cases.jsonl`. Bộ 60 case đã được commit trước `rules.py` làm bằng chứng nhãn không bị chỉnh theo kết quả. Vì vậy **không sửa nhãn** của bộ 60 case. Input (ví dụ `mo_ta`) chỉ được sửa khi có lý do rõ, ví dụ lộ đáp án, và phải ghi vào nhật ký §13. File corpus không tính vào 60 case, vào bảng phân bổ hay vào 50/10.
- **10 case** từ 3 repo Next.js + Supabase công khai, ghi ẩn danh `repo-01..03`: 7 case đợt 1 (27/11) và 3 case đợt 2 (28/11). Mọi case đều là `split=dev` và đều nằm trong `DOT_2` của `eval/build_benchmark.py`.

  | Case | Trọng tâm |
  |---|---|
  | `dt-r01-001` | C3: phiếu khám có chẩn đoán, sinh hiệu |
  | `dt-r02-001` | C1: ghi âm cuộc gọi gửi Gemini và Anthropic. C2 bẫy: repo có bảng đồng ý, nhưng không phải của khách bị ghi âm |
  | `dt-r02-002` | C2 đủ bằng chứng: bảng đồng ý tiếng Việt, khoá theo SĐT/email; kèm C1 gửi email qua Resend |
  | `dt-r02-003` | C3: GPS chấm công nhân viên |
  | `dt-r02-004` | C1, bẫy chatbox: hệ thống tự gắn họ tên vào prompt |
  | `dt-r03-001` | C3, bẫy: toạ độ là của trường, chưa dùng |
  | `dt-r03-002` | C1 âm tính: email mời gửi qua Supabase Auth, không tính theo XN6 đã chốt |
  | `dt-r01-002` (đợt 2) | C3: đơn thuốc + ảnh siêu âm, **giả định** hộ kinh doanh, 2.000 bệnh nhân → `MAT_MIEN_TRU` trên code thật |
  | `dt-r02-005` (đợt 2) | C3 bẫy, tag `vt`: cột `vi_tri` là thứ hạng Google (SEO), số liệu tổng hợp, không có dữ liệu cá nhân |
  | `dt-r02-006` (đợt 2) | C1 bẫy chatbox: nhân viên gõ đơn của khách vào Telegram rồi gửi sang Anthropic → `KICH_HOAT`, không phải `CAN_LUAT_SU` |

- **Quy tắc riêng:**
  - Ghi `nhan.nguon = "data_that: corpus/repo-NN"`.
  - `nhom_con` có dạng `<C1|C2|C3>_corpus`. `nhom_con_goc` là ô tương ứng trong bảng phân bổ (ví dụ `C2_du`), để validator chạy cùng luật kiểm như 60 case.
  - Validator dò URL repo và danh sách từ cấm trên **toàn bộ dòng**. Danh sách từ cấm để ở `data/corpus/denylist.txt`, mỗi dòng một từ (tên repo, tác giả, thương hiệu). Thư mục `data/corpus/` đã gitignore, **không commit** file này, vì chính nó chứa định danh.
  - Không ghi tên hay URL repo. Thay tên thương hiệu, tên trường, tên công ty bằng mô tả chung. Bỏ tiền tố schema có mang tên repo.
  - Schema và code là trích đoạn thật, ghi đúng số dòng. Không thêm bảng hay cột không có trong repo.
  - Danh sách URL chỉ để trên máy, không commit. Code của repo không commit.
- **Loại hình:** repo công khai không cho biết loại hình hay số chủ thể, nên mọi case ghi `loai_hinh=khong_ro`, `so_chu_the_luy_ke=null`, và C3 là `CAN_NGUOI_XAC_NHAN`. Đây là đúng thực tế khi quét `repo:`.
- **Ngoại lệ có giả định (`dt-r01-002`):** để thử `MAT_MIEN_TRU` trên code thật (góp ý CP3 của Khoa), nhóm **giả định** loại hình và quy mô: hộ kinh doanh, 2.000 chủ thể. Giả định được ghi nguyên văn trong `mo_ta` ("Giả định của nhóm để thử C3 (repo không ghi)…") và trong `ly_do`, không lấy từ repo. Script dựng corpus chặn mọi case có kết luận C3 khác `CAN_NGUOI_XAC_NHAN` mà không có câu giả định này.
- **Ẩn danh đợt 2:** tên file migration của repo-01 có tên repo, nên được bỏ khỏi đường dẫn (giữ số dòng thật). Không lấy dòng prompt có tên nhân viên bán hàng của repo-02.
- **Thứ tự làm:** dán nhãn tay và **commit nhãn trước**, sau đó mới chạy hệ thống trên các case này.
- **Giới hạn:** repo-03 xử lý dữ liệu trẻ em (Luật 91 Điều 24), nằm ngoài phạm vi C1–C3.

## 13. Nhật ký sửa nhãn

Ghi **mọi** lần sửa sau commit đầu tiên: sửa nhãn, và cả sửa input của case đã có trong benchmark. Mỗi lần ghi giờ, đổi gì, vì sao, ai duyệt. Lý do phải có **trước khi** xem output của hệ thống trên case đó.

| Giờ (27/11/2026) | Case | Sửa gì | Lý do | Người duyệt |
|---|---|---|---|---|
| 19:11 (`4f4fe9b`) | `c1-ro-008`, `c1-ro-005` | **Chỉ `mo_ta` (input).** Bỏ câu báo trước đây là câu tấn công. Nhãn, schema, code giữ nguyên. Trong benchmark chỉ ô `input` của `c1-ro-008` đổi, `expected` giữ nguyên. Làm trước CP2. | Input lộ đáp án, chế độ LLM được lợi không công bằng. Không phải sửa vì kết quả hệ thống. | Khoa (review PR #5) |
| 19:18 | `dt-r02-001` | **Nhãn C2:** `KHONG_KICH_HOAT` → `KICH_HOAT` (căn cứ thêm `Luat91 D9.3`, `ND356 D6`); cập nhật `bang_chung`, `ly_do`; `do_kho` → `hard`. Trong benchmark, ô `expected` đổi theo (chạy `build_benchmark.py --cho-sua-expected=dt-r02-001`, **trước CP2**, câu chưa vào `main`). | Hiểu sai phạm vi bản ghi đồng ý: bảng `dong_y_du_lieu` chỉ được form lead ghi vào, không có bằng chứng khách bị ghi âm đã đồng ý. Sửa **trước khi** ai chạy hệ thống trên case này. | Minh phát hiện (review PR #5); **Khoa duyệt** 27/11, trước khi merge PR #5 (duyệt qua trao đổi nhóm ngoài GitHub, Thịnh xác nhận) |
| 19:18 | `dt-r01-001`, `dt-r02-003` | Chỉ `ly_do`: gộp 2 câu kết luận C3 bị lặp. Bỏ câu "không còn miễn trừ", vì câu này mâu thuẫn với trường hợp doanh nghiệp lớn (không thuộc diện miễn). Trạng thái giữ nguyên. | Lý do viết chưa chính xác | Minh (review PR #5) |
| 19:18 | 7 case corpus | Thêm trường `nhom_con_goc` để validator chạy cùng luật kiểm như 60 case. Trạng thái giữ nguyên. | Kiểm nhất quán | Minh (review PR #5) |
