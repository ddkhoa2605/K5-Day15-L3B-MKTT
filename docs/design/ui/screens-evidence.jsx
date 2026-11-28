// S3 Bằng chứng · S4 Phân loại cột · S5 Cần luật sư rà soát

function Decide({ id }) {
  const { state, set } = useApp();
  const v = state.decisions[id];
  const pick = (x) => set({ decisions: { ...state.decisions, [id]: x } });
  return (
    <div className="stack" style={{ "--gap": "10px" }}>
      <span className="panel-label">Bạn đồng ý với phát hiện này không?</span>
      <div className="row">
        <button type="button" className="btn btn--primary" onClick={() => pick("xac_nhan")}>{v === "xac_nhan" ? "✓ Đã xác nhận" : "Xác nhận"}</button>
        <button type="button" className="btn" onClick={() => pick("bac_bo")}>{v === "bac_bo" ? "Đã bác bỏ" : "Bác bỏ, đây là dương tính giả"}</button>
      </div>
      {v === "bac_bo" && <p className="xs muted">Lý do bác bỏ được ghi vào nhật ký để tính tỉ lệ báo động giả.</p>}
    </div>
  );
}

function Hop({ role, label, file, from, to, hits, pin, tag, note }) {
  const f = SHP.files[file];
  return (
    <div className="hop">
      <span className={"role " + role}>{label}</span>
      <div className="sheet">
        <div className="file-tag"><span className="num muted">{f.path} · dòng {hits.join(", ")}</span>{tag && <span className="xs" style={{ fontWeight: 600, color: "var(--color-cool)" }}>{tag}</span>}</div>
        <Code file={file} from={from} to={to} hits={hits} pin={pin} />
        {note && <div className="ai-note">{note}</div>}
      </div>
    </div>
  );
}

const GROUP_KIND = { c1: "C1 · Chuyển dữ liệu xuyên biên giới", c2: "C2 · Xin và lưu sự đồng ý", c3: "C3 · Miễn trừ Điều 38" };

function ScreenBangChung({ which = "c1" }) {
  const { state } = useApp();
  const r = state.result;
  if (!r) return <NeedStep what="kết quả phân tích" />;
  const x = r.ket_qua[which.toUpperCase()];
  const ai = r.che_do !== "rule";

  return (
    <div className="screen">
      <div className="wrap page">
        <Back />
        <div className="row" style={{ "--gap": "8px", marginBottom: 28 }}>
          {GROUPS.map(([g, c]) => (
            <a key={c} className={"btn btn--sm" + (which === c ? " btn--ink" : "")} href={"#/bang-chung/" + c}><Pin c={c} size="sm" />{g}</a>
          ))}
        </div>
        <div className="grid-2r" style={{ gap: 40 }}>
          <div className="stack" style={{ "--gap": "22px" }}>
            <div className="row" style={{ "--gap": "10px" }}><span className="panel-label">{GROUP_KIND[which]}</span><Status s={x.trang_thai} /></div>
            <h1 style={{ fontSize: "clamp(28px, 3vw, 38px)" }}>{x.ten}</h1>
            <p style={{ color: "var(--color-ink-2)", fontSize: 17 }}>{x.giai_thich}</p>
            <div className="sheet" style={{ padding: "18px 22px" }}>
              <div className="panel-label" style={{ marginBottom: 10 }}>Căn cứ, do rule engine chọn từ <span className="num">citations.json</span></div>
              <CanCu items={x.can_cu} />
            </div>
            <ul className="stack" style={{ "--gap": "8px", listStyle: "none", padding: 0, margin: 0 }}>
              {[x.han_chot && "Hạn: " + x.han_chot, x.muc_phat,
                "Điều khoản do rule engine chọn từ bảng JSON, model không sinh số điều, số khoản."].filter(Boolean).map((t, i) => (
                <li key={i} className="row small" style={{ "--gap": "10px", alignItems: "flex-start", flexWrap: "nowrap" }}><span className="cool" aria-hidden="true">✓</span><span>{t}</span></li>
              ))}
            </ul>
            {ACTIVE.has(x.trang_thai) && <Decide id={which} />}
          </div>

          <div className="bench">
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 18 }}>
              <h2 style={{ fontSize: 18, letterSpacing: "-0.02em" }}>Dòng code làm phát sinh</h2>
              <span className="xs muted">{ai ? "quét tĩnh + AI kiểm chứng" : "quét tĩnh, không gọi AI"}</span>
            </div>
            <Evidence items={x.bang_chung} pin={which} />
            {which === "c3" && <p className="small" style={{ marginTop: 14 }}><a href="#/phan-loai">Xem toàn bộ cột đã quét</a></p>}
            <div className="note note--cool" style={{ marginTop: 22 }}>Người kiểm tra đọc các đoạn trên và tự xác nhận. Nếu một đoạn sai, bấm Bác bỏ; quyết định được ghi ở phiên làm việc này.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScreenPhanLoai() {
  const { state, set } = useApp();
  const [filter, setFilter] = useState("all");
  const scan = state.scan;
  if (!scan) return <NeedStep />;
  // BE chỉ trả nhãn cho cột nhạy cảm (bằng chứng C3); các cột khác không có nhãn từ BE → không tự gán.
  const tagged = {};
  ((state.result && state.result.ket_qua.C3.bang_chung) || []).forEach((b) => { if (b.nhom) tagged[b.snippet] = b; });
  const cols = (scan.cot || []).map((c) => {
    const key = c.table + "." + c.column;
    const t = tagged[key];
    return { col: key, file: c.file, line: c.line, nhom: t ? t.nhom : null, conf: t ? t.do_tin_cay : null };
  });
  const sens = (n) => !!n && n in SHP.nhom;
  const groups = {
    all: () => true,
    sens: (c) => sens(c.nhom),
    check: (c) => sens(c.nhom) && c.conf != null && c.conf < 0.7,
    none: (c) => !c.nhom,
  };
  const count = (k) => cols.filter(groups[k]).length;
  const rows = cols.filter(groups[filter]);
  const colDecision = state.colDecisions;
  const pick = (col, v) => set({ colDecisions: { ...colDecision, [col]: v } });

  return (
    <div className="screen">
      <div className="wrap page">
        <Back />
        <div className="page-head">
          <div>
            <div className="meta"><span>{cols.length} cột</span><span>{count("sens")} nhạy cảm</span><span>{count("check")} cần xem</span><span>chế độ {scan.che_do}</span></div>
            <h1>Phân loại cột theo nhóm dữ liệu nhạy cảm</h1>
            <p className="lede">{state.result ? <>Cột được rule engine dùng làm bằng chứng C3 có nhãn và độ chắc; rule engine chỉ dùng nhãn từ <span className="num">0.7</span> trở lên. Các cột khác backend không trả nhãn riêng.</> : "Chưa phân tích: mới có danh sách cột từ quét tĩnh."}</p>
          </div>
        </div>

        <div className="row" style={{ "--gap": "8px", marginBottom: 18 }} role="group" aria-label="Lọc">
          {[["all", "Tất cả"], ["sens", "Nhạy cảm"], ["check", "Dưới ngưỡng"], ["none", "Không có nhãn"]].map(([k, l]) => (
            <button key={k} type="button" className={"btn btn--sm" + (filter === k ? " btn--ink" : "")} aria-pressed={filter === k} onClick={() => setFilter(k)}>
              {l} <span className="num" style={{ opacity: .7 }}>{count(k)}</span>
            </button>
          ))}
        </div>

        <div className="grid-2" style={{ gridTemplateColumns: "minmax(0, 8fr) minmax(0, 4fr)" }}>
          <div className="sheet table-box">
            <table className="table">
              <thead><tr><th>Cột</th><th>Phân loại đề xuất</th><th>Độ chắc</th><th>Quyết định của bạn</th></tr></thead>
              <tbody>
                {rows.length === 0 && <tr><td colSpan="4" className="muted">Không có cột nào trong nhóm này.</td></tr>}
                {rows.map((c) => {
                  const d = colDecision[c.col];
                  const needs = sens(c.nhom);
                  return (
                    <tr key={c.col} className={sens(c.nhom) && !d ? "needs" : undefined}>
                      <td><div className="num" style={{ fontWeight: 500 }}>{c.col}</div><div className="xs muted">{c.file.split("/").pop()} dòng {c.line}</div></td>
                      <td>{c.nhom
                        ? <><div style={{ fontWeight: 500, color: "var(--color-cool)" }}>{SHP.nhom[c.nhom] ? SHP.nhom[c.nhom][1] : c.nhom}</div><div className="xs muted num">{SHP.nhom[c.nhom] ? "ND356 D4" + SHP.nhom[c.nhom][0] : ""}</div></>
                        : <span className="xs muted">Không có nhãn từ backend</span>}</td>
                      <td>{c.conf != null ? <><div className="num">{Number(c.conf).toFixed(1)}</div><div className="xs muted">{c.conf >= 0.7 ? "rule engine dùng" : "dưới ngưỡng"}</div></> : <span className="xs muted">—</span>}</td>
                      <td>
                        {!needs ? <span className="xs muted">Không cần xem</span>
                          : d ? <button type="button" className={"chip " + (d === "dung" ? "chip--ok" : "chip--human")} style={{ border: 0, cursor: "pointer" }} onClick={() => pick(c.col, null)}>{d === "dung" ? "Đã xác nhận" : "Bạn sửa: sai nhãn"}</button>
                          : <div className="row" style={{ "--gap": "6px" }}>
                              <button type="button" className="btn btn--sm btn--ink" onClick={() => pick(c.col, "dung")}>Đúng</button>
                              <button type="button" className="btn btn--sm" onClick={() => pick(c.col, "sai")}>Sai</button>
                            </div>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="stack" style={{ "--gap": "16px" }}>
            <div className="panel" style={{ padding: "20px 22px" }}>
              <h3>11 nhóm nhạy cảm, Điều 4 NĐ 356</h3>
              <ul className="ruled" style={{ marginTop: 12 }}>
                {Object.entries(SHP.nhom).map(([k, [d, t]]) => {
                  const hit = cols.filter((c) => c.nhom === k).length;
                  return (
                    <li key={k} style={{ display: "grid", gridTemplateColumns: "26px 1fr", gap: 8, padding: "7px 0", fontSize: 13.5, color: hit ? "var(--color-ink)" : "var(--color-muted)", fontWeight: hit ? 600 : 400 }}>
                      <span className="num">{d}</span><span>{t}{hit > 0 && <span className="chip chip--found" style={{ marginLeft: 8, minHeight: 20 }}>{hit} cột</span>}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
            <div className="note note--human">
              <h4>Vì sao đây là chỗ AI cần thiết</h4>
              Từ điển từ khoá không bắt được tên cột viết tắt kiểu <span className="num">tt_sk</span>, <span className="num">ghi_chu_bn</span>. Bấm Đúng hoặc Sai chỉ lưu ở phiên trình duyệt này, chưa gửi về backend.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScreenLuatSu() {
  const { state } = useApp();
  const [copied, setCopied] = useState(false);
  const c1 = state.result && state.result.ket_qua.C1;
  const live = c1 && c1.trang_thai === "CAN_LUAT_SU";
  const question = "Khi người dùng tự nhập nội dung vào ô chat của ứng dụng chúng tôi vận hành, và nội dung đó được gửi tới nền tảng AI đặt ngoài lãnh thổ Việt Nam, hành vi này có thuộc trường hợp \"chủ thể dữ liệu tự chuyển dữ liệu của mình\" tại khoản 6 Điều 20 Luật 91/2025/QH15 hay không?";
  const copy = () => { navigator.clipboard && navigator.clipboard.writeText(question); setCopied(true); setTimeout(() => setCopied(false), 1800); };
  return (
    <div className="screen">
      <div className="wrap page">
        <Back />
        {live ? (
          <div className="sheet" style={{ padding: "18px 22px", marginBottom: 26 }}>
            <div className="row" style={{ "--gap": "10px", marginBottom: 8 }}><Chip kind="human">Lượt quét này</Chip><Status s="CAN_LUAT_SU" /></div>
            <p style={{ fontSize: 16 }}>{c1.giai_thich}</p>
            <div style={{ marginTop: 12 }}><CanCu items={c1.can_cu} /></div>
            <div style={{ marginTop: 12 }}><Evidence items={c1.bang_chung} pin="c1" /></div>
          </div>
        ) : (
          <div className="note note--plain row" style={{ marginBottom: 26, "--gap": "10px" }}>
            <Chip kind="line">Ví dụ trạng thái</Chip>
            <span className="small">Lượt quét hiện tại không rơi vào trạng thái này. Phần dưới minh hoạ khi rule engine trả <span className="num">CAN_LUAT_SU</span> cho C1.</span>
          </div>
        )}
        <div className="grid-2" style={{ gap: 32 }}>
          <div className="stack" style={{ "--gap": "22px" }}>
            <div className="sheet" style={{ padding: "26px 28px", boxShadow: "0 0 0 1px var(--color-ink), var(--shadow-lift)" }}>
              <div className="row" style={{ "--gap": "10px", marginBottom: 10 }}><Pin c="c1" open /><span className="panel-label">C1 · Hệ thống từ chối kết luận</span><Status s="CAN_LUAT_SU" /></div>
              <h1 style={{ fontSize: "clamp(28px, 3vw, 40px)" }}>Cần luật sư rà soát</h1>
              <p style={{ marginTop: 12, fontSize: 17, color: "var(--color-ink-2)" }}>Dữ liệu gửi ra ngoài là chữ người dùng tự nhập. Có thể thuộc trường hợp không phải đánh giá tác động tại khoản 6 Điều 20. Công cụ không đủ căn cứ để quyết định.</p>
              <div style={{ marginTop: 16 }}><Cite code="Luat91 D20.6" /></div>
            </div>
            <div className="panel">
              <h3>Vì sao không đủ căn cứ</h3>
              <ol className="ruled" style={{ marginTop: 12, listStyle: "none" }}>
                {["Dòng dữ liệu bắt đầu từ ô nhập liệu, không phải từ cột trong database.", "Khoản 6 không định nghĩa thế nào là \"chính chủ thể tự chuyển\" khi ô chat do tổ chức vận hành.", "Người dùng có thể gõ thông tin của người khác; khi đó \"dữ liệu của chính mình\" không còn đúng."].map((t, i) => (
                  <li key={i} style={{ display: "grid", gridTemplateColumns: "28px 1fr", fontSize: 15 }}><span className="num" style={{ color: "var(--color-accent-text)" }}>{i + 1}</span><span>{t}</span></li>
                ))}
              </ol>
            </div>
            <div className="bench" style={{ padding: 18 }}>
              <Hop role="sink" label="Nguồn" file="route" from={7} to={7} hits={[7]} pin="c1" tag="người dùng nhập" note={<>Biến <span className="num">msg</span> đến từ body request, đi vào nội dung gửi ở dòng 12.</>} />
            </div>
          </div>

          <div className="stack" style={{ "--gap": "18px" }}>
            <div className="panel">
              <h3>Câu hỏi cần người trả lời</h3>
              <p className="small muted" style={{ margin: "4px 0 14px" }}>Chuyển nguyên văn cho luật sư hoặc cán bộ pháp chế.</p>
              <blockquote style={{ margin: 0, padding: "16px 18px", background: "var(--color-paper-3)", borderRadius: 8, fontSize: 15 }}>{question}</blockquote>
              <button type="button" className="btn btn--block" style={{ marginTop: 14 }} onClick={copy}>{copied ? "Đã chép" : "Sao chép câu hỏi"}</button>
            </div>
            <div className="panel">
              <h3>Trong khi chờ</h3>
              <ul className="ruled" style={{ marginTop: 12 }}>
                {["Phát hiện này không vào hồ sơ nháp; hồ sơ ghi nó là mục chờ rà soát pháp lý.", "Các đường đi đã xác nhận ở C1 vẫn có hiệu lực, không phụ thuộc kết luận này.", "Ghi lại câu trả lời của luật sư để lần quét sau không hỏi lại."].map((t, i) => <li key={i} className="small" style={{ padding: "10px 0" }}>{t}</li>)}
              </ul>
            </div>
            <div className="note note--cool">Trạng thái này do rule engine sinh ra, không phải lỗi. Metric <span className="num">tu_choi_dung</span> đo đúng việc này.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ScreenBangChung, ScreenPhanLoai, ScreenLuatSu, Hop });
