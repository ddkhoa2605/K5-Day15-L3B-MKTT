# Data card — dữ liệu bản chạy thử dùng

> Bản đầu cho **CP2 (19:30 Thứ Sáu 27/11)**, bản đủ ở CP3. Chấm ở rubric R4. Người viết: Thắng (G3).
> Không commit dữ liệu cá nhân thật, nguyên file data BTC cấp, hay mã nguồn repo trong corpus.

## Dataset 1 · Kho văn bản luật dữ liệu cá nhân

| | |
|---|---|
| Dùng để làm gì | Nguồn để Khoa dựng bảng luật `data/legal/*.json` (K1); ngữ cảnh luật đưa vào prompt chế độ `llm` (M6) |
| Từ đâu | Văn bản công khai: Luật 91/2025/QH15 (PDF vplsdms.vn), Nghị định 356/2025/NĐ-CP (HTML luatvietnam.vn), bản tin EY về Nghị định 330/2026/NĐ-CP (PDF). URL và sha256 ở `data/legal/SOURCES.md` |
| Xử lý những bước gì | Tải bằng GET · trích text (`pypdf` cho PDF, `html.parser` cho HTML) · chuẩn hoá Unicode NFC, sửa lỗi font `ƣ`→`ư` · bỏ header/footer lặp · cắt phần ký/nơi nhận · tách theo Điều rồi khoản. Script: `scripts/crawl_legal.py` |
| Số dòng / số đoạn | `chunks.jsonl`: **391 chunk** — Luat91 39 điều / 173 chunk · ND356 42 điều / 203 chunk · ND330 15 đoạn bản tin |
| Phiên bản / ngày lấy | Tải 27/11/2026 |
| Nhãn | Thật, công khai |
| Giới hạn | **ND330 chỉ là bản tin của EY, không phải toàn văn** → không dùng làm căn cứ điều khoản, mã ND330 để `can_cu: []` khi chưa có văn bản gốc. ND356 là bản trình bày lại của luatvietnam.vn, không phải Công báo. PDF Luật 91 còn ~20 chỗ chữ bị tách do `pypdf` (vd `khô ng`) → khoản dùng làm căn cứ phải so tay với PDF |

## Dataset 2 · 60 case có nhãn

| | |
|---|---|
| Dùng để làm gì | Đáp án biết trước để đo C1/C2/C3 và mã căn cứ; dữ liệu cho ablation `rule` · `llm` · `hybrid`; nguồn câu thử `tu_viet` cho `eval/benchmark.csv` |
| Từ đâu | Nhóm tự viết (Thịnh, T1, có Claude Code hỗ trợ soạn). File: `data/cases/cases.jsonl`, mô tả: `data/cases/LABELING.md` |
| Xử lý những bước gì | Viết kịch bản theo bảng phân bổ ô `nhom_con` · dán nhãn đủ 3 nhóm C1/C2/C3 cho mọi case · đồng bộ mã căn cứ với `data/legal/*.json` · kiểm cấu trúc bằng `python data/cases/validate_cases.py` |
| Số dòng / số đoạn | **60 case**: c3-vt 12 · c1-ro 8 · c2-thieu 7 · c1-am 6 · c3-ro 6 · c3-am 6 · c3-lk 6 · c2-du 5 · c1-chat 4 |
| Phiên bản / ngày lấy | 27/11/2026, commit `fd79b83` — **commit trước commit đầu tiên của `codebase/rules.py`** (lịch sử git chứng minh nhãn không chỉnh theo kết quả) |
| Nhãn | `synthetic` |
| Giới hạn | Nhãn do nhóm tự dán, **chưa được luật sư kiểm độc lập**. Data tự dựng **không phải bằng chứng pain**. Các cờ còn mở xem `LABELING.md` mục 6.4 |

**Data `synthetic` (nhóm tự sinh):**
- **Cách sinh:** viết tay theo bảng phân bổ ô `nhom_con` và quy trình dán nhãn ở `LABELING.md` mục 5, Claude Code hỗ trợ soạn. **Không** sinh bằng script ngẫu nhiên.
- **Seed:** không có (không dùng bộ sinh ngẫu nhiên).
- **Người kiểm:** Thịnh dán nhãn; `data/cases/validate_cases.py` kiểm cấu trúc, tính nhất quán nhãn, và quét giá trị thật (email, SĐT, dãy 12 số, số thẻ, API key). Minh và Khoa review ở PR #5; các lần sửa sau commit ghi ở `LABELING.md` mục 13.
- **Số dòng đã kiểm tay (ngoài người dán nhãn):** __ *(chưa ghi — Thịnh điền)*.
- Data tự dựng **không phải bằng chứng pain**.

## Dataset 3 · Repo demo

| | |
|---|---|
| Dùng để làm gì | Đầu vào `repo:data/demo_repos/…` cho buổi demo và kiểm luồng quét repo đầu-cuối |
| Từ đâu | Nhóm tự dựng (Thịnh, T3): `data/demo_repos/repo_a/`, `repo_b/`, `repo_c/`, mỗi repo có `supabase/migrations/001_init.sql` và 2–4 file `app/**/*.ts(x)` |
| Xử lý những bước gì | Cài sẵn kết quả mong đợi cho từng repo; không cần chạy được |
| Số dòng / số đoạn | 3 repo — **chưa có trên `main`** (kiểm 27/11 tối), điền số file ở CP3 |
| Phiên bản / ngày lấy | __ |
| Nhãn | `synthetic` |
| Giới hạn | Repo nhỏ, cố ý cài sẵn tín hiệu → dễ hơn repo thật; không dùng để đo độ chính xác |

## Dataset 4 · Corpus repo công khai Next.js + Supabase

Corpus có hai cách dùng, tách riêng để số thống kê không lẫn với nhãn:
**(4a)** 7 case dán nhãn tay cho benchmark, **(4b)** quét tự động để thống kê.

| | |
|---|---|
| Dùng để làm gì | (4a) nguồn câu thử `data_that: corpus/repo-NN` cho benchmark · (4b) đào bằng chứng pain trong `evidence/data-mining.md` (% repo gửi dữ liệu ra API nước ngoài, thiếu nhật ký đồng ý, chạm dữ liệu nhạy cảm) |
| Từ đâu | Repo công khai trên GitHub. repo-01 → repo-05 chọn tay (27/11, trước CP2). Các repo còn lại tìm qua GitHub Search API bằng `scripts/crawl_corpus.py`, ưu tiên repo do AI sinh (lovable, bolt.new, cursor) |
| Xử lý những bước gì | `git clone --depth 1` vào `data/corpus/repo-NN/` · lọc: có Next.js, có schema (`supabase/migrations/*.sql` hoặc `.sql` có `CREATE TABLE`), **≥5 file có chữ riêng của tiếng Việt** (ă đ ơ ư, dấu nặng/hỏi/ngã…) · **ẩn danh**: đã bỏ tên repo, URL, tác giả, thương hiệu và giá trị thật, chỉ ghi mã `repo-NN`. **Tên bảng và cột trong các case `data_that` được giữ nguyên** vì là đầu vào của benchmark đã khoá sau CP2; chúng có thể truy ngược về repo công khai bằng tìm kiếm mã (xem Giới hạn). Tài liệu bằng chứng (`evidence/`) chỉ mô tả bảng/cột bằng lời · (4b) quét tĩnh bằng `scanner` + `agent.answer` chế độ `rule` (`scripts/scan_corpus.py`) |
| Số dòng / số đoạn | (4a) **7 case từ 3 repo**: repo-01 (quản lý phòng khám) 1 case · repo-02 (quản trị nội bộ: chấm công, CRM, trợ lý AI) 4 case · repo-03 (quản lý lớp học của một trường) 2 case. Trọng tâm: C1 3 · C2 1 · C3 3. File `data/cases/corpus_cases.jsonl` · (4b) **35 repo** (5 chọn tay + 30 tự động), quét 27/11, kết quả ở `evidence/data-mining.md` |
| Phiên bản / ngày lấy | Tải 27/11/2026. (4a) commit `4f4fe9b` (PR #5) |
| Nhãn | Thật, đã ẩn danh. (4a) **nhãn dán tay** (Thịnh), **không** lấy từ output của hệ thống; số liệu chế độ `rule` ở (4b) chỉ dùng để thống kê, không dùng làm nhãn. Mã nguồn repo **không commit** (`data/corpus/` trong `.gitignore`); danh sách URL chỉ để trên máy |
| Giới hạn | **C3 của cả 7 case là `CAN_NGUOI_XAC_NHAN`**: repo công khai không cho biết loại hình doanh nghiệp hay số người dùng, nên không chốt được miễn trừ. **repo-03 xử lý dữ liệu trẻ em** (Luật 91 Điều 24), nằm ngoài phạm vi C1–C3. Case corpus để ở file riêng, không thêm vào `cases.jsonl`, vì bộ 60 case đã commit trước `rules.py` làm bằng chứng nhãn. Chỉ repo công khai → lệch về dự án học tập/portfolio. Chỉ phân tích tĩnh, không gọi endpoint, không chạy app → không biết dữ liệu thật có đi ra ngoài không. repo-01 → 05 chọn tay, không ngẫu nhiên. **Ẩn danh chưa trọn:** đã bỏ tên repo, URL, tác giả, thương hiệu và giá trị thật. **Tên bảng và cột trong các case `data_that` được giữ nguyên** vì là đầu vào của benchmark đã khoá sau CP2 (`data/cases/corpus_cases.jsonl`, `eval/benchmark.csv`); chúng có thể truy ngược về repo công khai bằng tìm kiếm mã, và cũng đã nằm trong lịch sử git của `main`. Nhóm chỉ công bố số tổng hợp, không công bố kết quả theo từng repo kèm tên bảng hay tên repo, và sẽ gỡ ngay nếu chủ repo yêu cầu |

**Ghi chú về bộ lọc (4b).** Lần chạy đầu lọc "tiếng Việt" bằng cả chữ `â ê ô` → lọt 19/40 repo tiếng Bồ Đào Nha, Pháp, Anh. Đã đổi sang chỉ chữ riêng của tiếng Việt + yêu cầu ≥5 file có chữ tiếng Việt; 19 repo bị loại ghi ở `data/corpus/rejected.json` (không commit). Kiểm tay 9 repo bộ quét gắn cờ "dữ liệu nhạy cảm" (trên 35 repo): 2 đúng chắc chắn (chẩn đoán ở phòng khám), 1 cần người xem (thông tin tài khoản ngân hàng), 6 báo nhầm (chẩn đoán lỗi thiết bị, vị trí xếp hạng SEO, chức danh công việc, toạ độ quán/câu lạc bộ) → số Z ở (4b) phải kiểm tay trước khi dùng.
