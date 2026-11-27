# Giả thuyết — viết TRƯỚC khi tìm bằng chứng

> Điền ở guide bước 1.1. Ôn lại: ngày 2 · lab ngày 2.
> Viết **trước** khi đọc dòng data đầu tiên hay hỏi người đầu tiên, để không sửa cho khớp kết quả. Kết quả ngược giả thuyết vẫn đủ điểm nếu số là thật.

## Ghi chú về thời điểm (đọc trước)

- **File này viết lúc 22:19 Thứ Sáu 27/11/2026**, tức **sau** khi đã quét corpus 35 repo (kết quả ở `evidence/data-mining.md`). Nhóm ghi rõ để không làm như thể viết trước.
- Phần giả thuyết ở mục 1 **không phải viết mới**: nó đã có trong `canvas.md` dòng 2–4, commit `39f6b60` lúc **16:46 27/11**, trước khi tìm repo đầu tiên (~17:00), và trong plan của nhóm (Task G3). Mục 1 chép lại đúng nội dung đó, không sửa theo kết quả.
- Mục 2 (ngưỡng "mình đúng nếu thấy") tách làm hai:
  - **Corpus:** ngưỡng đặt **sau** khi đã thấy số → chỉ dùng để mô tả, không coi là kiểm định.
  - **Phỏng vấn:** ngưỡng đặt **bây giờ, trước khi hỏi người đầu tiên** (chưa hẹn ai) → đây là phần kiểm định thật.

## 1. Giả thuyết (có từ 16:46 27/11, trước khi tìm bằng chứng)

- **Ngày giờ ghi lần đầu:** 27/11/2026 16:46 (`canvas.md`, commit `39f6b60`) · chép vào file này: 27/11/2026 22:19
- **Người dùng chính (một vai cụ thể):** freelancer / agency nhỏ dựng app Next.js + Supabase cho khách SME Việt Nam.
- **Mình nghĩ:** freelancer/agency gặp khó khi **phát hành app có dữ liệu người dùng Việt**, vì **họ không biết app đã kích hoạt nghĩa vụ pháp lý nào** — cụ thể là **chưa biết Luật 91 Điều 20 (chuyển dữ liệu cá nhân xuyên biên giới) áp cho cả lời gọi AI** gửi dữ liệu người dùng sang dịch vụ nước ngoài. Hậu quả là **bị khách hoặc nhà đầu tư hỏi mà không trả lời được**, và nghĩa vụ phát sinh mà không ai lập hồ sơ.
- **Có thể còn cách giải thích khác:**
  1. Họ **biết** nhưng bỏ qua vì app nhỏ, nghĩ mình được miễn (ND356 Điều 41) hoặc nghĩ chưa ai kiểm tra.
  2. Việc tuân thủ là của **khách hàng SME** (chủ dữ liệu), không phải của freelancer → freelancer không thấy đó là việc của mình.
  3. App của họ **ít khi** thật sự gửi dữ liệu cá nhân ra nước ngoài → pain C1 nhỏ hơn mình nghĩ, pain thật nằm ở chỗ khác (vd đồng ý, C2).
- **Nguồn sẽ dùng** (≥1 nguồn đạt ngưỡng, guide 1.2): [x] đào data · [x] phỏng vấn ≥3 · [ ] khảo sát ≥20 — nguồn chính: **quét 30–50 repo công khai Next.js + Supabase** · nguồn để kiểm lại: **3 phỏng vấn freelancer/agency** *(như canvas dòng 4)*.

## 2. Mình đúng nếu thấy

### 2a. Corpus — ngưỡng đặt SAU khi thấy số (chỉ mô tả, không phải kiểm định)

| Điều kiện | Kết quả corpus (N = 35, kiểm tay) | Ủng hộ giả thuyết? |
|---|---|---|
| Phần lớn app lưu dữ liệu cá nhân | 32/35 | Có (bối cảnh) |
| Phần lớn app gọi AI nước ngoài **kèm** dữ liệu cá nhân (C1) | 1/35 chắc chắn (11/35 gọi AI) | **Không** — ít hơn giả thuyết |
| Phần lớn app không lưu bằng chứng đồng ý (C2) | 32/35 không có chỗ lưu | Có — mạnh hơn giả thuyết |

→ Corpus nghiêng về **cách giải thích khác số 3**: pain lớn nhất trong code là **thiếu bằng chứng đồng ý (C2)**, không phải chuyển dữ liệu ra nước ngoài (C1). Kết luận đầy đủ ở `evidence/summary.md` mục 5.

### 2b. Phỏng vấn — ngưỡng đặt TRƯỚC khi hỏi (kiểm định thật)

*(Đặt lúc 22:19 27/11/2026. Chưa phỏng vấn ai. Không sửa ngưỡng sau khi có kết quả.)*

Với ≥3 freelancer/agency đã từng phát hành app có dữ liệu người dùng Việt:

- **Mình đúng nếu:** **≥2/3 người** trả lời *không* khi hỏi "Gửi họ tên/email của người dùng sang OpenAI/Gemini trong app có phải là chuyển dữ liệu cá nhân ra nước ngoài theo Luật 91 không?" — hỏi **trước** khi giải thích luật cho họ.
- **Mình sai (cách giải thích 1) nếu:** ≥2/3 người trả lời *có* nhưng vẫn không lập hồ sơ / không làm gì.
- **Mình sai (cách giải thích 2) nếu:** ≥2/3 người nói việc này là trách nhiệm của khách hàng, không phải của họ.
- **Đo thêm (không dùng để kết luận đúng/sai):** số lần bị khách hoặc nhà đầu tư hỏi về dữ liệu cá nhân trong 3 tháng qua; app gần nhất của họ có lưu lúc người dùng đồng ý (thời điểm + phiên bản điều khoản) không — để kiểm lại phát hiện C2 của corpus.

Câu hỏi phỏng vấn ghi theo `evidence/interviews/TEMPLATE.md`. **Chỉ ghi người thật đã nói chuyện, không bịa.**
