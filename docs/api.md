# API backend cho bản demo web — hợp đồng giữa BE (Minh) và FE

> Bản nháp 27/11/2026. BE viết bằng thư viện chuẩn Python (`http.server`), không cần `pip install`.
> Chạy: `SHP_UI=web python3 run.py` → `http://127.0.0.1:8000` (hoặc `python3 codebase/server.py`). Đổi cổng: `SHP_PORT=8080`.
> Không đặt `SHP_UI` thì `python run.py` vẫn là bản dòng lệnh (phương án dự phòng, spec §4). `answer()` không đổi; `eval`, `simulate` chạy như cũ.
> **Trang web của FE:** đặt file tĩnh (đã build) vào thư mục `web/` ở gốc repo, `web/index.html` là trang chính. Server trả chúng ở `/`, cùng địa chỉ với API → gọi API bằng đường dẫn tương đối `/api/...`, không cần CORS. Dev server riêng (vd Vite ở `localhost:5173`) vẫn gọi được nhờ CORS cho localhost.

## 1. Luồng màn hình

```
[1] Chọn đầu vào ──POST /api/scan──▶ [2] Xem trước "sẽ gửi gì ra ngoài" (CHƯA gọi AI)
                                          │ người dùng bấm "Gửi kiểm tra"
                                          ▼
                              POST /api/sessions/{id}/analyze  (gọi AI + rule engine)
                                          ▼
                                   [3] Kết luận C1, C2, C3
                                    │                    │
       sửa loại hình / số chủ thể   │                    │ bấm "Xác nhận kết luận"
POST /api/sessions/{id}/business ◀──┘                    ▼
   (chỉ chạy lại rule engine,              POST /api/sessions/{id}/confirm
    KHÔNG gọi lại AI) → [3]                  → [4] Bản nháp hồ sơ (nhãn BẢN NHÁP)
```

Nguyên tắc FE phải giữ (spec.md §4):
- Màn [2] hiện **đúng** danh sách `se_gui_ra_ngoai` trước khi người dùng bấm gửi. Không tự gọi `analyze` ngay sau `scan`.
- Màn [3] luôn hiện `giai_thich`, `can_cu`, `bang_chung` (file:dòng) của từng nhóm, và câu miễn trừ trách nhiệm `luu_y`.
- Nút xác nhận chỉ có ở màn [3]. Bản nháp luôn hiện nhãn "BẢN NHÁP", không có nút "nộp" hay "gửi".
- Không hiện từ "vi phạm", "đạt chuẩn", "an toàn". Dùng nguyên chữ BE trả về.

## 2. Quy ước chung

- Mọi request và response là JSON UTF-8 (`Content-Type: application/json`).
- Lỗi: HTTP 4xx/5xx với thân `{"loi": "<mã>", "thong_bao": "<câu cho người đọc>"}`.

  | HTTP | `loi` | Khi nào |
  |---|---|---|
  | 400 | `dau_vao_sai` | thiếu trường, sai kiểu, JSON hỏng, giá trị ngoài danh sách |
  | 400 | `tu_choi` | yêu cầu ngoài phạm vi (xin chứng nhận, tự nộp hồ sơ, câu hỏi tự do) — kèm `huong_dan` |
  | 404 | `khong_thay` | không có phiên, không có repo demo, link GitHub không tải được |
  | 409 | `sai_thu_tu` | gọi `business`/`confirm` trước khi `analyze` |
  | 413 | `qua_lon` | thân request > 28 MB, zip quá giới hạn |
  | 403 | `nguon_khong_cho_phep` | request từ trang web có Origin không được phép (xem CORS dưới đây) |
  | 500 | `loi_may_chu` | lỗi lạ phía BE (không lộ chi tiết nội bộ) |
  | 502 | `loi_model` | gọi model lỗi sau khi đã thử lại (BE đã che API key trong thông điệp) |

- Chỉ nhận request từ `http://localhost:*` và `http://127.0.0.1:*` (CORS). FE chạy ở địa chỉ khác thì đặt `SHP_CORS_ORIGIN=https://…` khi chạy BE. **Mở file HTML trực tiếp (`file://`, Origin `null`) bị chặn**: FE phải chạy bằng dev server trên localhost.
- BE chạy **một luồng**: trong lúc `analyze` (~5–15 giây) hoặc tải repo GitHub (tối đa 30 giây), mọi request khác phải chờ, kể cả `/api/health`.
- Phiên (`session_id`) lưu trong bộ nhớ BE, hết hạn sau 60 phút, tối đa 100 phiên. Khởi động lại BE là mất phiên.
- `analyze` gọi model thật nên mất khoảng 5–15 giây. FE hiện trạng thái chờ và **khoá nút** để không gửi hai lần.

## 3. Endpoint

### `GET /api/health`
```json
{"ok": true, "che_do": "hybrid", "model": {"provider": "openai", "phan_loai": "gpt-6-luna", "kiem_chung": "gpt-6.1-terra"}}
```

### `GET /api/demo-repos`
Danh sách repo demo có sẵn trên máy BE (thư mục `data/demo_repos/`).
```json
{"repos": [{"id": "repo_c", "mo_ta": "App đặt sân có bản đồ"}]}
```

### `GET /api/options`
Giá trị hợp lệ cho form loại hình doanh nghiệp.
```json
{"loai_hinh": [{"ma": "ho_kinh_doanh", "ten": "Hộ kinh doanh"}, {"ma": "doanh_nghiep_sieu_nho", "ten": "Doanh nghiệp siêu nhỏ"},
               {"ma": "doanh_nghiep_nho", "ten": "Doanh nghiệp nhỏ"}, {"ma": "khoi_nghiep", "ten": "Doanh nghiệp khởi nghiệp sáng tạo"},
               {"ma": "doanh_nghiep_lon", "ten": "Doanh nghiệp vừa, lớn"}, {"ma": "khong_ro", "ten": "Chưa rõ"}]}
```

### `POST /api/scan` — quét tĩnh, **không gọi AI**
Gửi **đúng một** trong bốn nguồn, kèm thông tin doanh nghiệp nếu đã biết:

```json
{"demo_repo": "repo_c"}
{"case": {"mo_ta": "...", "schema": ["users(id, email)"], "code": [{"file": "a.ts", "line": 3, "text": "..."}]}}
{"zip_base64": "<nội dung file .zip mã hoá base64>", "ten_file": "app.zip"}
{"github_url": "https://github.com/<owner>/<repo>"}

// tuỳ chọn, đi kèm bất kỳ nguồn nào:
{"loai_hinh": "doanh_nghiep_sieu_nho", "so_chu_the_luy_ke": 4200,
 "che_do": "hybrid"}   // "hybrid" (mặc định, có AI) hoặc "rule" (không gọi model, không gửi gì ra ngoài)
```

Giới hạn: zip ≤ 20 MB (**FE kiểm dung lượng trước khi tải lên**: request quá lớn bị BE ngắt trước khi đọc, trình duyệt có thể chỉ thấy lỗi kết nối thay vì JSON `413`); chỉ đọc file `.ts .tsx .js .jsx .mjs .cjs .sql .json .env.example`, mỗi file ≤ 200 KB; bỏ `node_modules`, `.next`, `.git`… `github_url` chỉ nhận `https://github.com/<owner>/<repo>` công khai, BE tải bản zip của nhánh mặc định (cần mạng).

Trả về `201`:
```json
{
  "session_id": "b1f0…",
  "nguon": {"loai": "demo_repo", "ten": "repo_c"},
  "mo_ta": "App đặt sân có bản đồ",
  "thong_ke": {"so_file": 6, "so_cot": 12, "so_loi_goi_ra_ngoai": 2},
  "cot": [{"table": "bookings", "column": "vi_tri_gan_nhat", "file": "supabase/migrations/001_init.sql", "line": 8}],
  "loi_goi_ra_ngoai": [{"file": "app/api/chat/route.ts", "line": 12, "loai": "ai_nuoc_ngoai", "dich": "api.openai.com",
                        "dong": "await openai.chat.completions.create({…})"}],
  "dong_y": {"bang": "consents", "du_3_truong": false, "tich_san": [{"file": "app/signup/page.tsx", "line": 30, "snippet": "…"}],
             "im_lang_dong_y": []},
  "se_gui_ra_ngoai": {
    "model_phan_loai": {"model": "gpt-6-luna", "noi_dung": ["mô tả app (đã lọc secret): App đặt sân có bản đồ",
                                                            "users.email (tên cột)", "bookings.vi_tri_gan_nhat (tên cột)"]},
    "model_kiem_chung": {"model": "gpt-6.1-terra", "noi_dung": ["app/api/chat/route.ts:7-17 (đoạn code đã lọc secret)"],
                         "doan_code": [{"file": "app/api/chat/route.ts", "tu_dong": 7, "den_dong": 17, "text": "… [REDACTED] …"}],
                         "kem_ten_cot_ca_nhan": "tên các cột được xếp là dữ liệu cá nhân ở bước phân loại"},
    "khong_gui": "Không gửi dữ liệu trong bảng, không gửi file khác, không gửi API key (đã thay bằng [REDACTED])."
  },
  "thieu_thong_tin": ["loai_hinh", "so_chu_the_luy_ke"],
  "canh_bao": ["Repo có 7 lời gọi ra ngoài, chỉ 5 lời gọi đầu được gửi model kiểm chứng."]
}
```
- `se_gui_ra_ngoai` là **toàn bộ** những gì `analyze` sẽ gửi cho model. Có test bảo đảm hai bên khớp. Phần nào không gửi thì là `null` (vd không có lời gọi ra ngoài → `model_kiem_chung: null`; `che_do: "rule"` → cả hai `null`).
- `thieu_thong_tin` rỗng khi đã có cả `loai_hinh` (khác `khong_ro`) và `so_chu_the_luy_ke`.

### `POST /api/sessions/{id}/analyze` — gọi AI + rule engine
Thân rỗng `{}`. Gọi lại lần hai trên cùng phiên trả kết quả đã có, **không** gọi model lại.

Trả về `200` (dùng chung khuôn với `business`):
```json
{
  "session_id": "b1f0…",
  "ket_qua": {
    "C1": {"ten": "Chuyển dữ liệu cá nhân ra nước ngoài (Điều 20 Luật 91)", "trang_thai": "KICH_HOAT",
           "giai_thich": "…", "can_cu": [{"ma": "Luat91 D20.1", "noi_dung": "…"}],
           "bang_chung": [{"file": "app/api/chat/route.ts", "line": 12, "snippet": "…"}],
           "han_chot": "60 ngày kể từ lần chuyển đầu tiên", "muc_phat": "Mức tối đa theo …"},
    "C2": {"…": "…"},
    "C3": {"…": "…", "nhom_nhay_cam": ["vi_tri_dinh_vi"]}
  },
  "da_gui_ra_ngoai": ["mô tả app (đã lọc secret)", "users.email (tên cột)", "app/api/chat/route.ts:7-17 (đã lọc secret)"],
  "thieu_thong_tin": ["loai_hinh", "so_chu_the_luy_ke"],
  "canh_bao": [],
  "luu_y": "Kết quả là gợi ý từ phân tích tĩnh mã nguồn để người chịu trách nhiệm xác nhận, không phải ý kiến pháp lý…",
  "bao_cao_text": "<toàn văn báo cáo dạng chữ, giống bản dòng lệnh>",
  "su_dung": {"so_lan_goi_model": 2, "token_vao": 1232, "token_ra": 618}
}
```

Giá trị `trang_thai`:

| Nhóm | Giá trị | Gợi ý hiển thị |
|---|---|---|
| C1 | `KICH_HOAT` · `KHONG_KICH_HOAT` · `CAN_LUAT_SU` | đỏ · xám · vàng |
| C2 | `KICH_HOAT_NANG` · `KICH_HOAT` · `KHONG_KICH_HOAT` | đỏ đậm · đỏ · xám |
| C3 | `MAT_MIEN_TRU` · `KHONG_THUOC_DIEN_MIEN` · `CON_MIEN_TRU` · `CAN_NGUOI_XAC_NHAN` | đỏ · đỏ · xám · vàng |

`KHONG_KICH_HOAT` nghĩa là **không thấy bằng chứng trong mã nguồn đã quét**, không có nghĩa là "an toàn".

### `POST /api/sessions/{id}/business` — sửa loại hình, số chủ thể
```json
{"loai_hinh": "doanh_nghiep_sieu_nho", "so_chu_the_luy_ke": 4200}
```
- `loai_hinh` thuộc danh sách ở `/api/options`; `so_chu_the_luy_ke` là số nguyên ≥ 0. Gửi một hoặc cả hai.
- Chỉ chạy lại rule engine trên kết quả AI đã có, **không gọi model** (`su_dung.so_lan_goi_model = 0`).
- Trả về cùng khuôn với `analyze`. Gọi trước `analyze` → `409 sai_thu_tu`, **nhưng thông tin vẫn được lưu** và dùng khi `analyze` chạy.

### `POST /api/sessions/{id}/confirm` — người chịu trách nhiệm xác nhận
Thân `{}`. Sinh bản nháp từ **kết luận mới nhất** của phiên (sau mọi lần `business`).
```json
{"ban_nhap_markdown": "BẢN NHÁP — chờ người chịu trách nhiệm duyệt. Không phải hồ sơ đã nộp.\n\n## Hồ sơ …",
 "ket_qua_da_xac_nhan": {"C1": "KICH_HOAT", "C2": "KICH_HOAT_NANG", "C3": "MAT_MIEN_TRU"}}
```
BE không gửi, không nộp bản nháp đi đâu.

### `GET /api/sessions/{id}`
Trạng thái phiên: `{"session_id", "buoc": "da_quet" | "da_phan_tich" | "da_xac_nhan", "nguon", "loai_hinh", "so_chu_the_luy_ke"}`.

### `POST /api/ask` — giống ô nhập của bản dòng lệnh
`{"text": "cấp giấy chứng nhận tuân thủ cho app tôi"}` → `400 tu_choi` kèm `huong_dan`. Dùng để demo nhánh tự từ chối. Đầu vào hợp lệ (`repo:…`, JSON) thì FE nên dùng `/api/scan`.

## 4. Không có trên web
- Chế độ `llm` (cấu hình B của ablation) — chỉ dùng để đo, không đưa cho người dùng.
- Đăng nhập, lưu lịch sử, nhiều người dùng đồng thời: BE chạy một luồng, dành cho demo trên một máy.
