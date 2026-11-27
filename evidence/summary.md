# Tổng hợp bằng chứng pain

> Bản đầu cho **CP2 (19:30 Thứ Sáu 27/11)**, bản đủ trước **CP3 10:00 Thứ Bảy 28/11**. Chấm ở rubric R1.
> Người viết: Thắng (G3). Giả thuyết: `evidence/hypothesis.md` (có từ 16:46 27/11 trong canvas; file viết lúc 22:19, ghi rõ thời điểm).
> **Trạng thái (28/11, trước CP3):** hai nguồn đạt ngưỡng — đào data corpus **N = 35 repo** (cách đếm chạy lại được, ≥5 ví dụ) và **khảo sát 31 phản hồi, 27 người đã dựng app** (≥20, ngoài nhóm; mục 2.4). **Phỏng vấn chưa có.**

## 0. Bốn pain mà `eval/metric_spec.yaml` trỏ về

Các trường `why` trong `metric_spec.yaml` (đã chốt ở CP2) trỏ về các pain dưới đây. Mỗi pain ghi bằng chứng hiện có và bằng chứng còn thiếu.

| # | Pain (không có chữ AI) | Metric trỏ về | Bằng chứng hiện có | Còn thiếu |
|---|---|---|---|---|
| P-a | **Không biết app đã kích hoạt nghĩa vụ nào**: freelancer đặt tên cột kiểu `tt_sk`, `vi_tri_gan_nhat`, gửi dữ liệu người dùng sang dịch vụ nước ngoài mà không nhận ra đó là chuyển dữ liệu xuyên biên giới | `phan_loai_viet_tat` | Corpus (mục 2.2): 32/35 repo lưu dữ liệu cá nhân cơ bản, 32/35 không có chỗ lưu sự đồng ý; 11/35 gọi AI nước ngoài. Bộ quét tự động gắn nhầm 6/9 cờ "nhạy cảm" → tên cột thật khó phân loại. Số nền B1, B4. **Khảo sát (n = 27, tự khai):** 24/27 chỉ "biết sơ qua" Luật 91 trở xuống; 13/27 gửi dữ liệu người dùng tới API AI nước ngoài và cùng lúc thu họ tên, email, SĐT; 15/27 nói có kiểm "tuân thủ pháp luật về dữ liệu" trước khi phát hành, nhưng 11 trong 15 người đó xin đồng ý bằng cách không chứng minh được (mục 2.4) | Phỏng vấn xác nhận "không biết" theo câu hỏi đặt trước ở `hypothesis.md` mục 2b |
| P-b | **Bị khách hoặc nhà đầu tư hỏi mà không trả lời được**: không chỉ ra được căn cứ điều khoản nào, dòng code nào | `trich_dan_dung` | Chưa có số về việc bị hỏi. Khảo sát chỉ có tín hiệu gián tiếp: 24/27 đã hỏi chatbot AI về nghĩa vụ dữ liệu, trong đó 15/27 "không chắc nó đúng" hoặc "phát hiện nó sai"; 24/27 chọn "trích đúng số điều, khoản" là tính năng quan trọng (ý kiến sau khi đọc mô tả sản phẩm) | Phỏng vấn: số lần bị hỏi / tháng, lần gần nhất mất bao lâu |
| P-c | **Tốn thời gian tra cứu cho cả những app không cần**: không biết app nào còn được miễn trừ (ND356 Điều 41) | `bao_dong_gia` | Chưa có bằng chứng cho pain "tốn thời gian". Bối cảnh từ corpus (không phải bằng chứng pain): sau kiểm tay chỉ 2/35 repo chạm dữ liệu nhạy cảm và 1/35 chắc chắn gửi dữ liệu cá nhân ra nước ngoài → nhiều app **không** kích hoạt C1/C3-nhạy cảm, nên công cụ cần phân biệt được thay vì báo đỏ đồng loạt. Khảo sát không hỏi thời gian tra cứu; chỉ cho bối cảnh: 18/27 app lớn nhất dưới 1.000 người dùng, không ai báo trên 100.000 → ngưỡng lũy kế hiếm khi chạm, mất miễn trừ chủ yếu đến từ dữ liệu nhạy cảm | Phỏng vấn: phút tra cứu / app (bằng chứng thật cho P-c) |
| P-d | **Hậu quả khi không biết nghĩa vụ**: mức phạt tối đa theo ND330 và Luật 91; hồ sơ nộp sai phải làm lại | `tu_choi_dung` | B4 (mục 2.1); mức phạt tối đa theo `data/legal/penalties.json` của Khoa | Nguồn gốc của B4 |

## 1. Nguồn đã dùng

| Nguồn | Đạt ngưỡng? | File |
|---|---|---|
| Đào data: corpus repo công khai Next.js + Supabase (x/N, %, cách đếm chạy lại được, ≥5 ví dụ) | ☑ N = 35, 10 ví dụ, script `scripts/crawl_corpus.py` + `scan_corpus.py` | `evidence/data-mining.md` |
| Phỏng vấn (≥3 freelancer/agency dựng app cho SME, ngoài nhóm) | ☐ chưa hẹn | `evidence/interviews/P1.md`… |
| Khảo sát (≥20 người ngoài nhóm, đúng người dùng) | ☑ 31 phản hồi, **27 người đã dựng app** trong 12 tháng qua (bạn bè đại học, học viên AI20K, ngoài nhóm); Google Form 17:00 27/11 – 05:00 28/11, một phần hỏi qua tin nhắn rồi nhóm nhập hộ vào form | `evidence/survey/questions.md`, `evidence/survey/results.csv` (đã bỏ email) |
| Nghiên cứu bàn giấy (số nền, không thay được bằng chứng của nhóm) | — | mục 2.1 dưới đây |

## 2. Số chính

### 2.1 Số nền từ nghiên cứu gốc

Các số này cho thấy app dựng nhanh bằng AI thường xử lý dữ liệu cá nhân thiếu cẩn thận. Phần lớn là số về **bảo mật**, không phải về **nghĩa vụ pháp lý**, nên chỉ dùng làm bối cảnh cho P-a. Bảo mật kỹ thuật (RLS, lộ key) nằm ngoài phạm vi của sản phẩm (xem `data/cases/LABELING.md` mục 2).

| Mã | Số | Nguồn gốc | Đã đọc bản gốc? |
|---|---|---|---|
| B1 | Escape.tech quét **hơn 5.600** app công khai dựng bằng nền tảng vibe coding, thấy **hơn 2.000** lỗ hổng, **hơn 400** secret bị lộ và **175** trường hợp lộ dữ liệu cá nhân (hồ sơ y tế, IBAN, số điện thoại, email). Front-end Lovable chứa JWT ẩn danh nối thẳng tới PostgREST của Supabase. | [Escape.tech — Methodology: How we discovered over 2k high-impact vulnerabilities in apps built with vibe coding platforms](https://escape.tech/blog/methodology-how-we-discovered-vulnerabilities-apps-built-with-vibe-coding/) | ☐ Số lấy qua kết quả tìm kiếm trích trang gốc. Công cụ tải trang bị chặn, **cần mở tay kiểm lại và ghi ngày đăng**. Lưu ý: Escape bán sản phẩm quét bảo mật. |
| B2 | Trong khoảng 20.000 repo công khai có dùng Copilot, **6,4%** lộ ít nhất một secret (trên 1.200 repo). Bản 2026: commit có AI đồng tác giả **dễ lộ secret gấp đôi**. | [GitGuardian — State of Secrets Sprawl 2025](https://www.gitguardian.com/state-of-secrets-sprawl-report-2025) · [2026](https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026/) | ☐ cần mở tay kiểm số |
| B3 | Thử 80 tác vụ viết code trên hơn 100 LLM: **45%** trường hợp code sinh ra có lỗ hổng bảo mật; JavaScript 38–45%. Bản 2026: **44%**. | [Veracode — press release 30/07/2025](https://www.veracode.com/press-release/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/) · [2026 GenAI Report Infographic](https://www.veracode.com/wp-content/uploads/2026-GenAI-Report-Infographic.pdf) | ☐ mới qua thông cáo báo chí; nên trích báo cáo đầy đủ |
| B4 | **Chưa đến 20%** hồ sơ đánh giá tác động chuyển dữ liệu cá nhân xuyên biên giới "đạt chuẩn". *Đây là số duy nhất nói thẳng về nghĩa vụ C1 (Luật 91 Điều 20).* | [VnEconomy](https://vneconomy.vn/chua-den-20-ho-so-danh-gia-tac-dong-chuyen-du-lieu-ca-nhan-xuyen-bien-gioi-dat-chuan.htm) | ☐ **mới đọc tiêu đề**. Cần mở bài để ghi: ai công bố (cơ quan nào), ngày, tổng số hồ sơ. Plan yêu cầu trích nguồn gốc, không trích trang tổng hợp, nên phải tìm văn bản hoặc phát biểu gốc. |

### 2.2 Đào data: corpus 35 repo

35 repo công khai Next.js + Supabase do người Việt dựng (5 chọn tay + 30 tìm tự động), quét tĩnh 27/11/2026 bằng `scanner.case_from_repo` + `agent.answer` chế độ `rule` của Minh, (bộ quét ở commit `f230a48`, trước #6 và #11), rồi **kiểm tay** từng repo bị gắn cờ. Số "không có chỗ lưu đồng ý" chỉ tính trong schema SQL. Chi tiết cách đếm, bảng đầy đủ và 10 ví dụ: `evidence/data-mining.md`. Số máy đếm chỉ để thống kê, không dùng làm nhãn.

| Đếm gì | Kết quả | Cách đếm |
|---|---|---|
| Lưu dữ liệu cá nhân cơ bản (SĐT, email, địa chỉ, họ tên, CCCD…) | **32/35 (91%)** | tên cột trong mọi file `.sql` |
| **Không có chỗ lưu sự đồng ý** (bảng hay cột consent) | **32/35 (91%)** | kiểm chéo tên cột rồi đọc tay từng kết quả; máy đếm 33/35 |
| Có nhật ký đồng ý gần đủ (người dùng + thời điểm + phiên bản) | **2/35** | kiểm tay; máy đếm 1/35 |
| Gọi AI nước ngoài | 11/35 (31%) | máy đếm, chưa kiểm từng lời gọi |
| Gửi dữ liệu cá nhân ra nước ngoài (C1) | **1/35** chắc chắn, +1 chưa rõ (máy đếm 3/35) | kiểm tay |
| Chạm dữ liệu nhạy cảm (ND356 Điều 4) | **2/35** chắc chắn, +1 cần người xem (máy đếm 9/35) | kiểm tay |

**Nghĩa với pain:** gần như mọi app lưu dữ liệu cá nhân, nhưng hầu như không app nào lưu bằng chứng đồng ý → nghĩa vụ C2 (Luật 91 Điều 9) dễ phát sinh mà người dựng không thấy. Ngược lại, C1 và C3-nhạy cảm chỉ chạm một phần nhỏ app → công cụ phải **phân biệt** được, không báo đỏ mọi app (P-c). Bộ quét tự động gắn nhầm 6/9 cờ "nhạy cảm" (chẩn đoán lỗi thiết bị, vị trí xếp hạng SEO, toạ độ quán cafe…) → tên cột thật khó phân loại đúng (P-a).

Ví dụ ban đầu từ 5 repo chọn tay (mã đã ẩn danh):
1. repo-01 (quản lý phòng khám): bảng bệnh nhân có số CCCD, ngày sinh, giới tính, SĐT, địa chỉ; có bảng chẩn đoán riêng.
2. repo-02 (quản trị nhân sự): số CCCD, lương cơ bản, mã số thuế, thuế thu nhập cá nhân của nhân viên.
3. repo-03 (quản lý lớp học): bảng liên kết và lời mời gắn học sinh với phụ huynh.
4. repo-04 (bán hàng + VNPay): SĐT, địa chỉ giao hàng.
5. repo-05 (POS bán lẻ + VietQR): khách hàng có SĐT, địa chỉ, công nợ.

### 2.3 Phỏng vấn

Chưa có. **Không điền số trước khi nói chuyện với người thật.**

| | Vai | Gặp pain? | Số lần / 1 tháng qua | Lần gần nhất mất | Đang xoay xở bằng |
|---|---|---|---|---|---|
| P1 | | | | | |
| P2 | | | | | |
| P3 | | | | | |

### 2.4 Khảo sát (31 phản hồi, n = 27 người đã dựng app)

Bộ câu hỏi, kênh và thời gian: `evidence/survey/questions.md`. Số liệu: `evidence/survey/results.csv`. Câu 1 lọc người dùng: 27/31 đã dựng hoặc tham gia dựng app có người dùng tại Việt Nam trong 12 tháng qua; 4 người còn lại bỏ trống các câu sau. **Mọi số dưới đây tính trên n = 27** và là **tự khai**. Khảo sát không đặt ngưỡng trước khi gửi, nên chỉ mô tả, không kiểm định giả thuyết.

**Ai trả lời:** lập trình viên trong doanh nghiệp 11/27, freelancer 9/27, agency/studio 4/27, tech lead/CTO startup 2/27, khác 1/27. Chỉ **13/27** đúng vai chính của giả thuyết (freelancer, agency); số còn lại là người dựng app trong doanh nghiệp hoặc startup. App gần nhất: cá nhân chưa đăng ký kinh doanh 13/27, doanh nghiệp nhỏ/khởi nghiệp 5/27, hộ kinh doanh 3/27, doanh nghiệp vừa hoặc lớn 3/27, siêu nhỏ 2/27, không rõ 1/27. App lớn nhất: dưới 1.000 người dùng 18/27, 1.000–10.000 4/27, 10.000–100.000 2/27, không rõ 3/27.

**Phần hành vi và hiểu biết (dùng làm bằng chứng):**

| Đếm gì | Kết quả | Liên quan |
|---|---|---|
| Thu họ tên, email, SĐT | **25/27 (93%)** | bối cảnh |
| Gửi hoặc lưu dữ liệu người dùng ở ít nhất một dịch vụ nước ngoài (API AI, email, analytics, database) | **21/27 (78%)**; không rõ 5/27 | C1 |
| · trong đó gửi tới **API AI** nước ngoài | 14/27 (52%); **13/27** vừa gửi API AI vừa thu họ tên/email/SĐT | C1 |
| · gửi email qua dịch vụ nước ngoài | 7/27 | C1 |
| · database hoặc server ở nước ngoài | 9/27 *(ngoài phạm vi C1 của sản phẩm theo XN6: không tính hạ tầng nền)* | — |
| Xin đồng ý bằng cách **chứng minh được** (lưu database kèm thời gian và phiên bản chính sách) | **6/27 (22%)** | C2 |
| Xin đồng ý bằng cách **không chứng minh được** | **19/27 (70%)**: "tiếp tục sử dụng nghĩa là đồng ý" 9, checkbox đã tích sẵn 5, không xin 5; không rõ 2 | C2 |
| Thu ít nhất một loại dữ liệu có thể nhạy cảm (GPS/bản đồ 10, thẻ/ví/giao dịch 7, khuôn mặt/vân tay/eKYC 3, sức khỏe 1) | **14/27**; thêm theo dõi hành vi 11/27 | C3 |
| Hiểu biết về Luật 91 và các nghị định | chưa nghe 11, nghe tên 2, biết sơ qua 11 → **24/27 (89%) từ "biết sơ qua" trở xuống**; hiểu khá rõ 2, đã áp dụng vào app 1 | P-a |
| Nói có kiểm "tuân thủ pháp luật về dữ liệu" trước khi phát hành | 15/27; **trong 15 người này, 11 xin đồng ý bằng cách không chứng minh được** và 12 chỉ "biết sơ qua" trở xuống | P-a |
| 3 người "hiểu khá rõ" hoặc "đã áp dụng vào app" | cả 3 dùng checkbox tích sẵn hoặc không xin đồng ý | P-a |
| Lo ngại app chưa đáp ứng quy định (4–5 trên thang 5) | 16/27 (59%) | bối cảnh |
| Đã hỏi chatbot AI về nghĩa vụ dữ liệu | 24/27; trong đó "không chắc nó đúng" 11, "phát hiện nó sai" 4, "thấy hữu ích" 9 | P-b (gián tiếp) |

**Phần ý kiến sau khi đọc mô tả sản phẩm (tín hiệu yếu, không phải bằng chứng pain):**
- Hữu ích (thang 5): 3 điểm 14/26, 4–5 điểm 11/26, 1 điểm 1/26 (1 người bỏ trống) → phần đông chỉ đánh giá trung bình.
- Tính năng quan trọng (chọn tối đa 3): trích đúng số điều, khoản 24/27; chỉ ra dòng code làm bằng chứng 16/27; cảnh báo mất miễn trừ 11/27; báo khi nào cần luật sư 8/27; sinh hồ sơ nháp 7/27; không gửi code ra nước ngoài 6/27.
- Giá mỗi tháng: chỉ dùng nếu miễn phí 11/27, dưới 200.000 đ 13/27, 200.000–500.000 đ 3/27. Người quyết chi: tự mình 14/27, khách hàng 5/27, founder/CEO 5/27.

**Giới hạn:** mẫu là bạn bè đại học và học viên AI20K, không chọn ngẫu nhiên, lệch về người trẻ và app nhỏ; chỉ 13/27 là freelancer hoặc agency. Câu trả lời tự khai, người trả lời có thể không biết chính xác app gửi gì ra ngoài. Một phần câu trả lời được hỏi qua tin nhắn rồi nhóm nhập hộ vào form. Câu tự do lặp lại nguyên văn nhiều lần (mục 3).

## 3. ≥5 trích dẫn hoặc ví dụ nguyên văn (có nguồn, bỏ tên)

**Trích nguyên văn từ code và schema của corpus** (repo công khai, mã repo đã ẩn danh; tên bảng hoặc đường dẫn đặc thù đã đổi sang tên chung theo `data/cases/LABELING.md` §12, nội dung dòng code và số dòng là thật; nguồn: `data/cases/corpus_cases.jsonl`, case ghi trong ngoặc):

1. **repo-01, quản lý phòng khám** (`dt-r01-001`). Schema bảng phiếu khám: `checkups(id, customer_id, doctor_id, checkup_date, symptoms, diagnosis, conclusion, notes, heart_beat, blood_pressure, temperature, weight, height, recheck_date)`, và `app/[locale]/(app)/checkups/actions.js:50`: `diagnosis: get("diagnosis"),` → triệu chứng, chẩn đoán, huyết áp là tình trạng sức khoẻ (ND356 Điều 4 điểm d); repo không có nơi lưu đồng ý của bệnh nhân.
2. **repo-02, quản trị nhân sự** (`dt-r02-003`). `app/cham-cong/page.tsx:162`: `const id = navigator.geolocation.watchPosition(` và dòng 164: `setGps({ lat: p.coords.latitude, lng: p.coords.longitude, accuracy: p.coords.accuracy });` → vị trí của nhân viên xác định qua dịch vụ định vị của thiết bị (điểm h), lưu vào `attendance.check_in_lat/lng` theo ngày.
3. **repo-02, trợ lý AI nội bộ** (`dt-r02-004`). `components/ai-assistant.tsx:77`: `body: JSON.stringify({ query: q, path: pathname, role: user.role, name: user.full_name })` và `app/api/ai-chat/route.ts:32`: `` - Tên: ${name} `` → hệ thống tự gắn họ tên từ hồ sơ đăng nhập vào prompt gửi Anthropic (C1), không phải người dùng tự gõ.
4. **repo-02, trợ lý giao việc** (`dt-r02-008`). `lib/tro-ly/giao-viec.ts:27`: `` .map((u) => `- ${u.full_name} (${u.position || "nhân viên"})`) `` và `lib/tro-ly/goi-ai.ts:49`: `const API_URL = "https://api.anthropic.com/v1/messages";` → họ tên và chức vụ của mọi nhân viên được ghép vào system prompt gửi ra nước ngoài (C1).
5. **repo-02, form lead** (`dt-r02-002`). `lib/du-lieu-ca-nhan.ts:125`: `phien_ban: o.phienBan || PHIEN_BAN_DONG_Y, ip: o.ip || null, ua: o.ua ? String(o.ua).slice(0, 300) : null, meta: o.meta || null,` → một trong **2/35** repo có nhật ký đồng ý gần đủ (khoá theo SĐT/email, có phiên bản, mục đích, thời điểm).
6. **repo-02, thống kê SEO** (`dt-r02-005`). Schema: `seo_theo_url(ngay, url, clicks, impressions, ctr, vi_tri)` → `vi_tri` là **thứ hạng trên Google**, không phải vị trí của người *(bộ quét báo nhầm)*.
7. **repo-03, quản lý lớp học** (`dt-r03-001`). `supabase/migrations/0031_school_networks_checkin.sql:13`: `-- GPS geofence: chuẩn bị sẵn schema, CHƯA dùng (lat/lng/bán kính mét).` → toạ độ là của khuôn viên trường và chưa dùng, không phải vị trí cá nhân *(bộ quét báo nhầm)*.

Các ví dụ khác (repo-14 gửi email qua Resend, repo-17 bảng consents, repo-41 số tài khoản người bán, repo-10 và repo-27 toạ độ quán) ở `evidence/data-mining.md` mục 4, dạng mô tả.

**Câu trả lời nguyên văn từ khảo sát** (câu 16, "điều gì sẽ khiến bạn tiếp tục dùng"; 15/27 người trả lời câu này; đây là ý kiến về sản phẩm, không phải mô tả pain):
- "Quét nhanh, chỉ đúng đoạn code gây rủi ro và trích đúng điều luật để sửa trước khi release, không báo sai quá nhiều." (1 người)
- "Công cụ giúp tôi tránh khỏi các vi phạm mà luật nhà nước mới ban hành" (4 người, trùng nguyên văn)
- "bảo mật thông tin" (4 người, trùng nguyên văn)
- "nếu miễn phí và hiệu quả" (6 người, trùng nguyên văn)

Trích dẫn từ phỏng vấn: chưa có.

## 4. Các nguồn có khớp nhau không

Corpus nói: 32/35 app lưu dữ liệu cá nhân, 32/35 không có chỗ lưu sự đồng ý, chỉ 2/35 có nhật ký đồng ý gần đủ, 31% gọi AI nước ngoài. Khớp hướng với số nền B1–B3 (app dựng nhanh xử lý dữ liệu cá nhân thiếu cẩn thận), dù B1–B3 nói về bảo mật chứ không về nghĩa vụ. Lệch: corpus cho thấy C1 (gửi dữ liệu cá nhân ra nước ngoài) **ít hơn** giả thuyết — chỉ 1/35 chắc chắn sau kiểm tay. Phỏng vấn cần trả lời vì sao: không biết, hay biết mà bỏ qua.

**Khảo sát so với corpus:**
- **Khớp ở C2:** corpus 32/35 repo không có chỗ lưu đồng ý, 2/35 có nhật ký gần đủ; khảo sát 19/27 xin đồng ý bằng cách không chứng minh được, 6/27 lưu kèm thời gian và phiên bản. Hai nguồn độc lập cùng chỉ ra thiếu bằng chứng đồng ý là phổ biến.
- **Lệch ở C1:** khảo sát có 13/27 người tự khai gửi dữ liệu người dùng tới API AI nước ngoài và thu họ tên/email/SĐT; corpus chỉ chứng minh được 1/35 repo gửi dữ liệu cá nhân ra nước ngoài (11/35 gọi AI). Có ba cách giải thích, chưa phân biệt được: (1) corpus là repo công khai, lệch về đồ án, còn khảo sát hỏi app thật gần nhất; (2) bộ quét bỏ sót lời gọi qua wrapper; (3) người trả lời coi mọi lời gọi AI là "gửi dữ liệu người dùng" dù không kèm dữ liệu cá nhân. Câu hỏi khảo sát không tách được ba trường hợp này.
- **Lệch ở dữ liệu nhạy cảm:** khảo sát 14/27 thu ít nhất một loại có thể nhạy cảm, corpus chỉ 2/35 chắc chắn sau kiểm tay. Lựa chọn trong form rộng hơn định nghĩa ND356 Điều 4 (ví dụ "tìm gần tôi" không chắc là vị trí cá nhân xác định qua định vị; "ví" không chắc là tài khoản ngân hàng), nên 14/27 là cận trên.
- **Phần "không biết" của giả thuyết:** khảo sát gợi ý ủng hộ (24/27 chỉ biết sơ qua trở xuống; 11/15 người nói có kiểm tuân thủ vẫn xin đồng ý bằng cách không chứng minh được), nhưng câu hỏi khác câu kiểm định đặt trước ở `hypothesis.md` mục 2b, nên không thay được phỏng vấn.

## 5. Kết luận

Giả thuyết ở `evidence/hypothesis.md` — *"freelancer/agency dựng app cho SME chưa biết Điều 20 áp cho lời gọi AI"*: **phải đổi một phần**: kết quả corpus gợi ý pain C2 lớn hơn C1, trong khi giả thuyết đặt trước nhấn vào C1. *(Các "cách giải thích khác" ở `hypothesis.md` mục 1b viết sau khi đã thấy số corpus, nên không dùng để nói kết quả này đã được dự đoán.)* Phần "không biết" chưa kiểm được bằng code, chờ phỏng vấn theo ngưỡng đã đặt trước ở `hypothesis.md` mục 2b.
- **Đúng hơn dự kiến ở C2**: thiếu bằng chứng đồng ý là chuyện gần như mọi app — corpus 32/35 không có chỗ lưu, khảo sát 19/27 xin đồng ý bằng cách không chứng minh được. Đây là kết luận vững nhất vì hai nguồn độc lập cùng chỉ ra.
- **C1 chưa rõ**: corpus mới chứng minh được 1/35 repo gửi kèm dữ liệu cá nhân ra nước ngoài, nhưng khảo sát có 13/27 người tự khai gửi dữ liệu người dùng tới API AI nước ngoài. Hai nguồn lệch nhau và chưa phân biệt được nguyên nhân (mục 4), nên **không** kết luận C1 nhỏ hay lớn.
- **"Không biết" có tín hiệu ủng hộ nhưng chưa kiểm định**: 24/27 chỉ biết sơ qua Luật 91 trở xuống, và cả những người nói có kiểm tuân thủ phần lớn vẫn xin đồng ý không đúng cách. Kiểm định đặt trước (phỏng vấn, `hypothesis.md` mục 2b) chưa làm.
- **Nhu cầu trả tiền yếu**: 11/27 chỉ dùng nếu miễn phí, 13/27 chọn dưới 200.000 đ/tháng; mức hữu ích phần đông là 3/5. Đây là ý kiến sau khi đọc mô tả, chỉ là tín hiệu.

Điều vẫn chưa biết:
- Bộ quét bỏ sót bao nhiêu ở C1 và dữ liệu nhạy cảm (kiểm ngẫu nhiên 5–10 repo không bị gắn cờ).
- Vì sao khảo sát và corpus lệch ở C1 (cần hỏi tiếp người đã khai gửi dữ liệu tới API AI: gửi trường nào).
- Freelancer có biết Điều 20 áp cho lời gọi AI không, và bao lâu bị khách hỏi một lần (phỏng vấn).

## Lịch hẹn (dùng cho CP2 — chỉ ghi vai và giờ, không tên)

| Vai | Giờ hẹn | Đã xong? |
|---|---|---|
| Freelancer dựng app Next.js + Supabase cho SME | __ | ☐ |
| Agency nhỏ (2–5 người) | __ | ☐ |
| Tech lead startup chuẩn bị gọi vốn | __ | ☐ |
