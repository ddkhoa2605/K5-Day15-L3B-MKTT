# Nguồn văn bản luật (Task G1)

Sinh bởi `python scripts/crawl_legal.py`. Chỉ tải trang công khai bằng GET, User-Agent `ship-hop-phap-crawler`.
`sha256_goc` là hash của file tải về (PDF/HTML), `sha256_txt` là hash của `raw/<key>.txt` sau khi làm sạch.

| Văn bản | Tên | URL | Loại | Toàn văn? | Ngày tải | Số điều | sha256_goc | sha256_txt |
|---|---|---|---|---|---|---|---|---|
| Luat91 | Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 | https://vplsdms.vn/upload/post/L_91_2025_QH15.pdf | pdf | có | 2026-11-27 | 39 | `70e246bb134c70c5dd158c1df65fc7a73ff7e5801a7f77ee238f1bc5c76db09c` | `ad7109d5d2a283dedcce6706b09a3ce23a84e69120de129a2bb0127a5e4068e1` |
| ND356 | Nghị định 356/2025/NĐ-CP hướng dẫn Luật Bảo vệ dữ liệu cá nhân | https://luatvietnam.vn/dan-su/nghi-dinh-356-2025-nd-cp-quy-dinh-chi-tiet-luat-bao-ve-du-lieu-ca-nhan-422896-d1.html | html | có | 2026-11-27 | 42 | `457fff9ef63d7fd8f5e247d1867a2c1e9e9e3baf8e3d0a3a5daf9bcba3dc3595` | `936c3763147dad1e74267141d80a111fead18622f0da7f1d681921c4368f1d2c` |
| ND330 | Nghị định 330/2026/NĐ-CP xử phạt VPHC về bảo vệ dữ liệu cá nhân (bản tin EY) | https://www.ey.com/content/dam/ey-unified-site/ey-com/vi-vn/technical/tax/documents/ey-vn-decree-330-providing-sanctions-for-personal-data-protection.pdf | pdf | **không** | 2026-11-27 | 0 | `df5406551149e1c860e5091eeffc2290a6de9ee42c27d4b54c6d347a5d4e3b74` | `f0eb4b84bf988e1e1462543ccd5b72ec0d2d24590bc0f8ee7698f4712443dd55` |

## Lưu ý

- **ND330 chỉ là bản tin tóm tắt của EY, không phải toàn văn Nghị định 330/2026/NĐ-CP.** Mã điều khoản ND330 trong `citations.json` phải đối chiếu văn bản gốc; chưa có thì để `can_cu: []`, không đoán.
- ND356 lấy từ bản HTML của luatvietnam.vn (bản sao trình bày lại, không phải Công báo). Trang wincolaw không tìm được; thuvienphapluat.vn chặn tải tự động (403).
- Luật 91 lấy từ PDF do vplsdms.vn đăng lại.
- Text trích tự động (pypdf/html.parser) có thể lỗi ngắt dòng. PDF Luật 91 còn ~20 chỗ chữ bị tách (vd `khô ng`, `liệ u`) do pypdf; không sửa tự động để tránh làm hỏng từ đúng. Điều khoản dùng làm căn cứ cần so tay với bản gốc.
