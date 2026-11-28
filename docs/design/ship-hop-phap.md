---
name: So Kiem
slug: ship-hop-phap
genre: modern-minimal
paper: dark 17 250
display: grotesk-sans Be Vietnam Pro
accent: chromatic-amber 80
posture: restrained
keywords: compliance, audit, legal, privacy, personal data, scanner, static analysis, devtools, evidence, record, obligation, consent, report, cli, tuan thu, du lieu ca nhan, nghia vu, phap ly, bang chung, quet ma nguon
material: graphite ground in three lightness steps, pale ink, hairline panels cut from one surface, Be Vietnam Pro 500 for what a person reads, JetBrains Mono for what the scanner found, amber for a person who must confirm and cool blue for the scanner
photo: duotone paper-3 ink
---

# So Kiem

Theme cho Ship Hợp Pháp, chỉnh từ theme Console của Hallmark (MIT, Together AI). Một cuốn sổ kiểm do người cẩn thận giữ: nền graphite ba bậc sáng, panel viền mảnh cắt từ một mặt, Be Vietnam Pro cho chữ người đọc, JetBrains Mono cho thứ máy quét tìm thấy (file:dòng, tên cột, sink, mã điều luật), amber cho người phải xác nhận, xanh lạnh cho máy. Không phải terminal neon, không phải bảng cảnh báo đỏ rực, không phải con dấu chứng nhận.

## Tokens

```css
:root {
  --color-paper: oklch(17% 0.008 250); --color-paper-2: oklch(21% 0.009 250); --color-paper-3: oklch(13.5% 0.007 250);
  --color-ink: oklch(95% 0.005 250); --color-ink-2: oklch(83% 0.008 250); --color-muted: oklch(71% 0.01 250);
  --color-rule: oklch(31% 0.01 250); --color-rule-2: oklch(42% 0.012 250);
  --color-accent: oklch(82% 0.15 80); --color-accent-ink: oklch(18% 0.04 75); --color-accent-soft: oklch(29% 0.05 80); --color-focus: oklch(82% 0.15 80);
  --color-cool: oklch(77% 0.12 245); --color-cool-soft: oklch(29% 0.05 245);
  --color-ok: oklch(76% 0.15 150); --color-ok-soft: oklch(24.5% 0.03 150); --color-bad: oklch(70% 0.17 25); --color-bad-soft: oklch(24.5% 0.035 25);
  --font-display: "Be Vietnam Pro", ui-sans-serif, system-ui, sans-serif; --font-body: var(--font-display);
  --font-outlier: "JetBrains Mono", ui-monospace, monospace;
  --radius-card: 10px; --radius-pill: 6px; --rule-hair: 1px;
  --shadow-card: none;
  --tracking-display: -0.025em; --display-weight: 500;
}
```

Một nút chỉnh, colourway, ghi trong stamp (`so-kiem: graphite`): `graphite` là token trên, cho demo trên màn hình; `paper` là nền oklch(98% 0.006 85), ink oklch(19% 0.010 60), amber oklch(54% 0.14 70), cool oklch(52% 0.14 250), dùng cho `demo-slides.pdf` và máy chiếu. Ở mọi colourway, amber là người, cool là máy.

## Type

- **Display:** Be Vietnam Pro 500, `--tracking-display`, line-height 1.08 (dấu tiếng Việt chồng hai tầng cần chỗ), sentence case, roman; không bao giờ 700.
- **Body:** Be Vietnam Pro 400 ở 16 đến 17px, line-height 1.6, màu `--color-muted`; câu dẫn màu `--color-ink-2`.
- **Labels, captions, table heads, chips:** Be Vietnam Pro 500 nhỏ hơn một bậc, sentence case, màu `--color-muted`.
- **Measured:** JetBrains Mono 400 và 500 ở 14 đến 15px, `slashed-zero`, số tabular, cho thứ hệ thống viết ra: `app/api/chat/route.ts:12`, tên cột, run ID, token, chi phí, mã `Luat91 D20.6`. Không bao giờ là label, head hay nút.

## Surfaces

- Panel viền mảnh: 1px `--color-rule`, bên trong `--color-paper-2`, radius 10px (6px cho control). Panel đứng cạnh nhau là một mặt chia bằng rule 1px; `--color-rule-2` đánh dấu dòng đang chọn hoặc gáy của một trail.
- Ba bậc, không đèn: nền, panel cao hơn một bậc, bậc sâu nhất cho code, log, đoạn ±5 dòng đã redact. Không shadow, glow, gradient.
- Band: `--color-paper-3` hoặc `--color-paper-2`, không nền amber; tối đa hai band.
- Ảnh: dự án không có ảnh thật; chỉ dùng ảnh chụp output dòng lệnh thật, đen trắng, radius 10px, viền 1px, chú thích bên dưới. Không ảnh người, không ảnh stock về luật (búa, cán cân).

## Range

- **Bằng chứng:** đoạn code ±5 dòng trên bậc sâu nhất, dòng làm phát sinh nghĩa vụ trên `--color-cool-soft`, bên cạnh là điều luật và một câu giải thích bằng lời người.
- **Con số:** một giá trị lớn bằng mặt measured (32/35 repo, chi phí / task thành công, tỉ lệ đạt), nguồn và run ID bên dưới bằng cool, giá trị cũ gạch ngang phía trên nếu đã sửa.
- **Trail:** dòng theo gáy 1px `--color-rule-2`: lượt eval, thay đổi spec §10, ai duyệt (amber), lúc nào (cool), vì sao (ink).
- **Panel:** C1, C2, C3 cắt từ một mặt với đường nối 1px, mỗi panel chứa đúng output thật của `report.py`, không phải hình minh hoạ.

## Controls

- Cặp nút: nền amber chữ `--color-accent-ink` (hành động của người: xác nhận, duyệt bản nháp) cạnh nút viền 1px `--color-rule-2` trên `--color-paper-2`, đều 6px.
- Chip chỉ mang trạng thái: `CAN_NGUOI_XAC_NHAN`, `CAN_LUAT_SU`, `BẢN NHÁP` trên `--color-accent-soft`; `PHAT_SINH`, `KHONG_PHAT_SINH` trên `--color-cool-soft`. Input trên `--color-paper-3`; link gạch dưới `--color-rule-2`, hover thành amber.
- Ok và bad chỉ cho kết quả eval đạt / trượt và diff, không cho nghĩa vụ.

## Motion

Giá trị đổi qua `--dur-short` trên `--ease-out`; biểu đồ vẽ một lần. Không reveal, parallax, hover nhấc.

## Voice

Sổ kiểm của người cẩn thận: con số, đơn vị, nguồn, ai ký. Số chưa có ghi `(chưa đo)`, số tự tính ghi `(tự ước tính)` màu muted; không bịa số. Nói "nghĩa vụ đã phát sinh", không nói "vi phạm" hay "đạt chuẩn".

## Do-nots

- Không tô đỏ một nghĩa vụ đã phát sinh; phát sinh nghĩa vụ không phải vi phạm, và báo đỏ mọi thứ là lỗi của các scanner mà dự án muốn tránh.
- Không đổi nghĩa màu; một kết quả máy quét màu amber là đang nói dối người phải xác nhận.
- Không con dấu, khiên hay chữ "certified"; công cụ không cấp chứng nhận tuân thủ.
- Không mono cho label, head hay nút; mono là thứ máy viết.
- Không font thiếu subset `vietnamese` (Host Grotesk, Atkinson Mono của Console đều thiếu); dấu rơi về font hệ thống là lỗi ngay trên slide.

## Build hint

```html
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500&family=JetBrains+Mono:wght@400;500&subset=vietnamese&display=swap" rel="stylesheet">
```

```css
h1, h2, h3 { font-family: var(--font-display); font-weight: var(--display-weight); letter-spacing: var(--tracking-display); line-height: 1.08; }
.panels { display: grid; gap: var(--rule-hair); background: var(--color-rule); border: var(--rule-hair) solid var(--color-rule); border-radius: var(--radius-card); overflow: hidden; }
.panels > * { background: var(--color-paper-2); }
.measured { font-family: var(--font-outlier); font-size: var(--text-sm); font-variant-numeric: tabular-nums slashed-zero; }
.reading { font-family: var(--font-outlier); font-size: var(--text-display); letter-spacing: -0.04em; line-height: 1; color: var(--color-ink); }
.evidence { background: var(--color-paper-3); font-family: var(--font-outlier); }
.evidence .hit { background: var(--color-cool-soft); }
.row--minus { background: var(--color-bad-soft); } .row--plus { background: var(--color-ok-soft); }
.btn { border: var(--rule-hair) solid var(--color-rule-2); border-radius: var(--radius-pill); padding: var(--space-sm) var(--space-md); background: var(--color-paper-2); color: var(--color-ink); font-weight: 500; transition: background-color var(--dur-short) var(--ease-out); }
.btn--confirm { background: var(--color-accent); border-color: var(--color-accent); color: var(--color-accent-ink); }
::selection { background: color-mix(in oklab, var(--color-accent) 25%, transparent); }
```
