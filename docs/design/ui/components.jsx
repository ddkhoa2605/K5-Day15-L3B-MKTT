// Các mảnh dùng chung cho mọi màn. Theme: docs/design/ship-hop-phap.md
const { useState, useEffect, useMemo, useRef, createContext, useContext } = React;

const AppCtx = createContext(null);
const useApp = () => useContext(AppCtx);

function Brand() {
  return (
    <a className="brand" href="#/quet">
      <svg viewBox="0 0 22 22" aria-hidden="true">
        <rect x="1.5" y="1.5" width="19" height="19" rx="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M6 8h10M6 12h6M6 16h8" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="16.5" cy="12" r="2.2" fill="oklch(70% 0.19 40)" />
      </svg>
      Lextrace
    </a>
  );
}

// Chỉ báo khi KHÔNG gọi được backend; nối được thì không hiện gì.
function BeStatus({ be }) {
  if (be.ok === false) return <span className="chip chip--human" title={be.err}>Không gọi được backend</span>;
  return null;
}

// Không có thanh bước: đi theo đúng luồng bằng nút ở cuối mỗi màn (quét → xem trước → kết quả → duyệt → hồ sơ).
function TopBar({ route, be }) {
  return (
    <header className="top">
      <div className="wrap">
        <Brand />
        <div className="top-end" style={{ marginLeft: "auto" }}>
          {be && <BeStatus be={be} />}
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

// ---- Phần dùng dữ liệu backend ----

const GROUPS = [["C1", "c1"], ["C2", "c2"], ["C3", "c3"]];
// Trạng thái coi là "đã phát sinh / cần người xử lý" → vào cổng duyệt
const ACTIVE = new Set(["KICH_HOAT", "KICH_HOAT_NANG", "MAT_MIEN_TRU", "KHONG_THUOC_DIEN_MIEN", "CAN_NGUOI_XAC_NHAN", "CAN_LUAT_SU"]);

// bang_chung của BE: [{file, line, snippet, nhom?, do_tin_cay?}]
function Evidence({ items, pin = "c1" }) {
  if (!items || !items.length) return <p className="small muted">Không có dòng bằng chứng nào trong mã nguồn đã quét.</p>;
  return (
    <div className="stack" style={{ "--gap": "12px" }}>
      {items.map((b, i) => (
        <div key={i} className="sheet">
          <div className="file-tag">
            <span className="num muted">{b.file} · dòng {b.line}</span>
            {b.nhom && <span className="xs" style={{ fontWeight: 600, color: "var(--color-cool)" }}>{nhomLabel(b.nhom)}{b.do_tin_cay != null ? " · " + Number(b.do_tin_cay).toFixed(1) : ""}</span>}
          </div>
          <div className="code">
            <div className="ln hit"><span className="no">{b.line}</span><span className="slot"><Pin c={pin} open /></span><span>{b.snippet || " "}</span></div>
          </div>
        </div>
      ))}
    </div>
  );
}

// can_cu của BE: [{ma, noi_dung}] — số điều khoản do rule engine chọn, FE chỉ hiện
function CanCu({ items }) {
  if (!items || !items.length) return <p className="small muted">Rule engine không gắn căn cứ cho trạng thái này.</p>;
  return (
    <ul className="ruled">
      {items.map((c) => (
        <li key={c.ma} style={{ padding: "10px 0" }}>
          <span className="num" style={{ fontSize: 13.5, fontWeight: 500 }}>{c.ma}</span>
          <p className="small" style={{ color: "var(--color-ink-2)", marginTop: 2 }}>{c.noi_dung}</p>
        </li>
      ))}
    </ul>
  );
}

function nhomLabel(n) {
  return SHP.nhom[n] ? SHP.nhom[n][1] + " (ND356 D4" + SHP.nhom[n][0] + ")" : n;
}

function ErrorNote({ err }) {
  if (!err) return null;
  return (
    <div className="note note--human" role="alert" style={{ marginTop: 16 }}>
      <h4>{err.status ? "Backend trả lỗi " + err.status + (err.loi ? " · " + err.loi : "") : "Không gọi được backend"}</h4>
      {err.message}
      {err.body && err.body.huong_dan && <p className="small" style={{ marginTop: 6 }}>{err.body.huong_dan}</p>}
    </div>
  );
}

function NeedStep({ what = "lượt quét", to = "quet", label = "Quét mới" }) {
  return (
    <div className="screen"><div className="wrap page">
      <h1>Chưa có {what}</h1>
      <p className="lede">Màn này hiện dữ liệu thật từ backend. Bắt đầu từ bước trước.</p>
      <a className="btn btn--primary" style={{ marginTop: 20 }} href={"#/" + to}>{label}</a>
    </div></div>
  );
}

function srcLabel(scan) {
  if (!scan || !scan.nguon) return "";
  return scan.nguon.loai + ": " + (scan.nguon.ten || "");
}

Object.assign(window, { AppCtx, useApp, TopBar, Pin, Status, STATUS, Chip, Code, Cells, Entry, Cite, NotMeasured, ActionBar, Back,
  GROUPS, ACTIVE, Evidence, CanCu, nhomLabel, ErrorNote, NeedStep, srcLabel });
