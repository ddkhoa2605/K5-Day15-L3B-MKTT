// Các mảnh dùng chung cho mọi màn. Theme: docs/design/ship-hop-phap.md
const { useState, useEffect, useMemo, useRef, createContext, useContext } = React;

const AppCtx = createContext(null);
const useApp = () => useContext(AppCtx);

const STEPS = [
  ["quet", "Quét mới"],
  ["dang-quet", "Đang quét"],
  ["ket-qua", "Kết quả"],
  ["duyet", "Cổng duyệt"],
  ["ho-so", "Hồ sơ nháp"],
];
const STEP_OF = { "bang-chung": "ket-qua", "phan-loai": "ket-qua", "luat-su": "ket-qua" };

function Brand() {
  return (
    <a className="brand" href="#/quet">
      <svg viewBox="0 0 22 22" aria-hidden="true">
        <rect x="1.5" y="1.5" width="19" height="19" rx="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M6 8h10M6 12h6M6 16h8" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="16.5" cy="12" r="2.2" fill="oklch(70% 0.19 40)" />
      </svg>
      Ship Hợp Pháp
    </a>
  );
}

function TopBar({ route }) {
  const current = STEP_OF[route] || route;
  return (
    <header className="top">
      <div className="wrap">
        <Brand />
        <nav className="steps-nav" aria-label="Các bước">
          {STEPS.map(([id, label], i) => (
            <a key={id} href={"#/" + id} aria-current={current === id ? "page" : undefined}>
              <span className="n">{i + 1}</span><span className="t">{label}</span>
            </a>
          ))}
        </nav>
        <div className="top-end">
          <a href="#/logic" aria-current={route === "logic" ? "page" : undefined}>Logic rule engine</a>
          <a href="#/ablation" aria-current={route === "ablation" ? "page" : undefined}>Ablation</a>
        </div>
      </div>
    </header>
  );
}

function Pin({ c, open, size, ring, label }) {
  const cls = ["pin", "pin--" + c, open && "open", size === "sm" && "pin--sm", ring && "pin--ring"].filter(Boolean).join(" ");
  return <span className={cls} aria-hidden={label ? undefined : "true"} role={label ? "img" : undefined} aria-label={label} />;
}

// Trạng thái từ rules.py → nhãn + kiểu chip. Không tô đỏ nghĩa vụ đã phát sinh.
const STATUS = {
  KICH_HOAT: ["Đã phát sinh", "found"],
  KICH_HOAT_NANG: ["Đã phát sinh, cách xin sai", "found"],
  MAT_MIEN_TRU: ["Mất miễn trừ", "found"],
  KHONG_THUOC_DIEN_MIEN: ["Không thuộc diện miễn", "found"],
  CAN_NGUOI_XAC_NHAN: ["Cần bạn xác nhận", "human"],
  CAN_LUAT_SU: ["Cần luật sư rà soát", "human"],
  KHONG_KICH_HOAT: ["Không phát sinh", "none"],
  CON_MIEN_TRU: ["Còn miễn trừ", "ok"],
};
function Status({ s }) {
  const [label, kind] = STATUS[s] || [s, "none"];
  return <span className={"chip chip--" + kind}>{label}</span>;
}

function Chip({ kind = "line", children }) {
  return <span className={"chip chip--" + kind}>{children}</span>;
}

function Code({ file, hits = [], pin = "c1", from, to }) {
  const f = SHP.files[file];
  const rows = f.lines.map((text, i) => ({ n: f.start + i, text }))
    .filter((r) => (from == null || r.n >= from) && (to == null || r.n <= to));
  return (
    <div className="code">
      {rows.map((r) => {
        const hit = hits.includes(r.n);
        return (
          <div key={r.n} className={"ln" + (hit ? " hit" : "")}>
            <span className="no">{r.n}</span>
            <span className="slot">{hit && <Pin c={pin} open />}</span>
            <span>{r.text || " "}</span>
          </div>
        );
      })}
    </div>
  );
}

function Cells({ items }) {
  return (
    <dl className="cells">
      {items.map(([k, v, opts = {}], i) => (
        <div key={i} className={"cell" + (opts.wide ? " wide" : "")}>
          <dt>{k}</dt>
          <dd className={opts.mono ? "num" : opts.text ? "text" : undefined}>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function Entry({ c, kind, where, title, cells, foot }) {
  return (
    <article className="entry">
      <div className="entry-head">
        <div className="entry-kind">
          <span className="k"><Pin c={c} size="sm" />{kind}</span>
          {where && <span className="num">{where}</span>}
        </div>
        <div className="entry-title">{title}</div>
      </div>
      <Cells items={cells} />
      {foot && <div className="entry-foot">{foot}</div>}
    </article>
  );
}

function Cite({ code, short }) {
  return (
    <div>
      <span className="num" style={{ fontSize: 13.5, fontWeight: 500 }}>{code}</span>
      {!short && <p className="small" style={{ color: "var(--color-ink-2)", marginTop: 2 }}>{SHP.cite[code]}</p>}
    </div>
  );
}

function NotMeasured({ night }) {
  return <span className="num" style={{ fontSize: 14, color: night ? "var(--color-night-muted)" : "var(--color-muted)" }}>(chưa đo)</span>;
}

function ActionBar({ children }) {
  return <div className="actionbar"><div className="wrap">{children}</div></div>;
}

function Back({ to = "ket-qua", label = "Kết quả" }) {
  return <a className="back" href={"#/" + to}><span aria-hidden="true">←</span>{label}</a>;
}

// C3 theo rules.evaluate_c3: fixture có cột nhạy cảm chắc chắn (vi_tri_gan_nhat, 1.0)
function c3Status(loaiHinh, luyKe) {
  if (loaiHinh === "doanh_nghiep_lon") return "KHONG_THUOC_DIEN_MIEN";
  if (loaiHinh === "khong_ro" || luyKe === "khong_ro") return "CAN_NGUOI_XAC_NHAN";
  return "MAT_MIEN_TRU";
}

Object.assign(window, { AppCtx, useApp, TopBar, Pin, Status, STATUS, Chip, Code, Cells, Entry, Cite, NotMeasured, ActionBar, Back, c3Status });
