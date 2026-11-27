# Ba repo demo (T3) — dữ liệu `synthetic`

Mỗi repo là một app Next.js + Supabase rút gọn, nhóm tự viết. Mỗi repo cài sẵn **đúng một tình huống**, để kiểm một nhánh luật qua đường `repo:` (`scanner.case_from_repo` → `agent.answer`).
- Repo **không cần chạy được**, chỉ cần trông như code thật: import đúng thư viện, cú pháp hợp lệ.
- Không chứa dữ liệu cá nhân thật, không chứa key.
- Phần giải thích được để **riêng ở file này**, không viết comment trong code. Lý do: scanner đọc cả comment, và comment kiểu "ô đồng ý tích sẵn" sẽ thành bằng chứng giả, đồng thời gợi ý đáp án cho model.

| Repo | App | Cài sẵn | `repo:data/demo_repos/…` phải ra |
|---|---|---|---|
| `repo_a` | Tiệm bánh online | Bảng `consents(user_id, accepted_at, policy_version)`; ô đồng ý mặc định trống (`useState(false)`); OpenAI chỉ nhận tên và mô tả sản phẩm, không nhận dữ liệu khách | C1 `KHONG_KICH_HOAT` · C2 `KHONG_KICH_HOAT` |
| `repo_b` | Shop đồ công nghệ, chat tư vấn AI | `app/api/chat/route.ts` ghép `profile.ho_ten` + `profile.email` vào prompt gửi OpenAI; có bảng `consents` đủ 3 trường | C1 `KICH_HOAT`, căn cứ `Luat91 D20.1` + `D20.2`, bằng chứng trỏ `app/api/chat/route.ts:13` · C2 `KHONG_KICH_HOAT` |
| `repo_c` (**demo chính**) | Đặt sân cầu lông, nút "Tìm sân gần nhất" | `bookings.vi_tri_gan_nhat` lưu toạ độ từ `navigator.geolocation`; không có nơi lưu đồng ý; ô đồng ý `defaultChecked` | C2 `KICH_HOAT_NANG` (`Luat91 D9.3`, `ND356 D6`, `ND356 D6.3`) · C3 có nhóm `vi_tri_dinh_vi` |

## C3 cần người dùng khai loại hình

Đầu vào `repo:` không cho biết loại hình doanh nghiệp hay số chủ thể. Vì vậy C3 của **cả ba repo** là `CAN_NGUOI_XAC_NHAN`, và hệ thống nhắc "hãy xác nhận để chốt C3". Đây là hành vi đúng (spec §4: AI gợi ý, người quyết).

Kịch bản demo repo C gồm 2 bước:
1. `repo:data/demo_repos/repo_c` → C3 `CAN_NGUOI_XAC_NHAN`, nhóm `vi_tri_dinh_vi`, kèm lời nhắc khai loại hình.
2. Gửi lại case dạng JSON (từ `scanner.case_from_repo`), kèm `"loai_hinh": "doanh_nghiep_sieu_nho", "so_chu_the_luy_ke": 4200` → C3 **`MAT_MIEN_TRU`** (`ND356 D4h`, `Luat91 D38.3`, `ND356 D41.2`). Thông điệp: "chỉ một cột `vi_tri_gan_nhat` làm doanh nghiệp siêu nhỏ mất miễn trừ, dù chỉ có 4.200 người dùng".

Kết quả chạy thật xem ở `eval/demo-check.md`.
