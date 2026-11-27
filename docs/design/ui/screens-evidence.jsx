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

function ScreenBangChung({ which = "c1" }) {
  const { state } = useApp();
  const hybrid = state.mode === "hybrid";
  const C = {
    c1: {
      kind: "C1 · Chuyển dữ liệu xuyên biên giới", status: "KICH_HOAT",
      title: "Email người dùng được gửi tới một nền tảng AI ngoài lãnh thổ",
      lede: "Thuộc trường hợp tại điểm c khoản 1 Điều 20: dùng nền tảng ở ngoài lãnh thổ Việt Nam để xử lý dữ liệu cá nhân thu thập tại Việt Nam.",
      cites: ["Luat91 D20.1", "Luat91 D20.2"],
      checks: ["Điều khoản do rule engine chọn từ bảng JSON, model không sinh số điều, số khoản.", "Mức phạt 30–50 triệu đồng (ND330 D56.1) là khung tối đa, không phải mức chắc chắn bị áp.", "Hạn: 60 ngày kể từ lần chuyển dữ liệu đầu tiên."],
    },
    c2: {
      kind: "C2 · Xin và lưu sự đồng ý", status: "KICH_HOAT_NANG",
      title: "Cách xin đồng ý không hợp lệ ở trang đăng ký",
      lede: "Ô đồng ý được tích sẵn, và trang coi việc tiếp tục sử dụng là đồng ý. Cả hai đều bị cấm.",
      cites: ["Luat91 D9.3", "ND356 D6", "Luat91 D9.4d", "ND356 D6.3"],
      checks: ["Mức phạt khung: 50–70 triệu đồng khi coi im lặng là đồng ý (ND330 D43.2b); 30–50 triệu đồng khi đặt mặc định đồng ý (ND330 D43.1c).", "Cá nhân bị phạt bằng một nửa mức của tổ chức.", "Nghĩa vụ về sự đồng ý không nằm trong miễn trừ của Điều 38."],
    },
  }[which];

  return (
    <div className="screen">
      <div className="wrap page">
        <Back />
        <div className="row" style={{ "--gap": "8px", marginBottom: 28 }}>
          <a className={"btn btn--sm" + (which === "c1" ? " btn--ink" : "")} href="#/bang-chung/c1"><Pin c="c1" size="sm" />C1</a>
          <a className={"btn btn--sm" + (which === "c2" ? " btn--ink" : "")} href="#/bang-chung/c2"><Pin c="c2" size="sm" />C2</a>
          <a className="btn btn--sm" href="#/phan-loai"><Pin c="c3" size="sm" />C3</a>
        </div>
        <div className="grid-2r" style={{ gap: 40 }}>
          <div className="stack" style={{ "--gap": "22px" }}>
            <div className="row" style={{ "--gap": "10px" }}><span className="panel-label">{C.kind}</span><Status s={C.status} /></div>
            <h1 style={{ fontSize: "clamp(28px, 3vw, 38px)" }}>{C.title}</h1>
            <p style={{ color: "var(--color-ink-2)", fontSize: 17 }}>{C.lede}</p>
            <div className="sheet" style={{ padding: "18px 22px" }}>
              <div className="panel-label" style={{ marginBottom: 10 }}>Căn cứ, lấy từ <span className="num">citations.json</span></div>
              <ul className="ruled">
                {C.cites.map((c) => <li key={c} style={{ padding: "10px 0" }}><Cite code={c} /></li>)}
              </ul>
            </div>
            <ul className="stack" style={{ "--gap": "8px", listStyle: "none", padding: 0, margin: 0 }}>
              {C.checks.map((t, i) => <li key={i} className="row small" style={{ "--gap": "10px", alignItems: "flex-start", flexWrap: "nowrap" }}><span className="cool" aria-hidden="true">✓</span><span>{t}</span></li>)}
            </ul>
            <Decide id={which} />
          </div>

          <div className="bench">
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 18 }}>
              <h2 style={{ fontSize: 18, letterSpacing: "-0.02em" }}>{which === "c1" ? "Đường đi từ cột dữ liệu tới lời gọi ra ngoài" : "Hai dòng làm phát sinh"}</h2>
              <span className="xs muted">{hybrid ? "xác nhận bởi static + AI" : "xác nhận bởi static"}</span>
            </div>
            {which === "c1" ? (
              <div className="path">
                <Hop role="source" label="Nguồn" file="sql" from={2} to={5} hits={[4]} pin="c1" tag="static ✓" />
                <Hop role="" label="Đọc" file="route" from={8} to={9} hits={[9]} pin="c1" tag="static ✓" />
                <Hop role="sink" label="Gửi đi" file="route" from={10} to={13} hits={[10, 12]} pin="c1" tag={hybrid ? "AI xác nhận" : "static ✓"}
                  note={<>Đích: <span className="num">api.openai.com</span>, đặt ngoài lãnh thổ Việt Nam. Trường mang theo: <span className="num">users.email</span> nối thẳng vào nội dung gửi.</>} />
              </div>
            ) : (
              <div className="path">
                <Hop role="" label="Dòng 5" file="signup" from={4} to={6} hits={[5]} pin="c2" tag="tích sẵn" note={<>Vi phạm <span className="num">ND356 D6.3</span>: thiết lập mặc định đồng ý.</>} />
                <Hop role="sink" label="Dòng 8" file="signup" from={7} to={9} hits={[8]} pin="c2" tag="im lặng" note={<>Vi phạm <span className="num">Luat91 D9.4d</span>: im lặng không phải đồng ý.</>} />
              </div>
            )}
            <div className="note note--cool" style={{ marginTop: 22 }}>Người kiểm tra đọc các đoạn trên và tự xác nhận. Nếu một đoạn sai, bấm Bác bỏ và lý do được ghi lại.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScreenPhanLoai() {
  const { state, set } = useApp();
  const [filter, setFilter] = useState("all");
  const sens = (n) => n in SHP.nhom;
  const groups = {
    all: () => true,
    sens: (c) => sens(c.nhom),
    basic: (c) => c.nhom === "pii_co_ban",
    none: (c) => c.nhom === "khong_ca_nhan",
    check: (c) => c.nhom === "khong_ro" || (sens(c.nhom) && c.conf < 0.7),
  };
  const count = (k) => SHP.columns.filter(groups[k]).length;
  const rows = SHP.columns.filter(groups[filter]);
  const label = (n) => sens(n) ? SHP.nhom[n][1] : n === "pii_co_ban" ? "Dữ liệu cá nhân cơ bản" : "Không phải dữ liệu cá nhân";
  const basis = (n) => sens(n) ? "ND356 D4" + SHP.nhom[n][0] : n === "pii_co_ban" ? "ngoài danh mục Điều 4" : "không khớp từ khoá";
  const colDecision = state.colDecisions;
  const pick = (col, v) => set({ colDecisions: { ...colDecision, [col]: v } });

  return (
    <div className="screen">
      <div className="wrap page">
        <Back />
        <div className="page-head">
          <div>
            <div className="meta"><span>8 cột</span><span>1 nhạy cảm</span><span>0 cần xem</span><span>chế độ {state.mode}</span></div>
            <h1>Phân loại cột theo nhóm dữ liệu nhạy cảm</h1>
            <p className="lede">Mỗi cột vào một nhãn kèm độ chắc. Độ chắc dưới <span className="num">0.7</span> tự rơi vào danh sách cần xem; rule engine chỉ dùng nhãn từ <span className="num">0.7</span> trở lên.</p>
          </div>
        </div>

        <div className="row" style={{ "--gap": "8px", marginBottom: 18 }} role="group" aria-label="Lọc">
          {[["all", "Tất cả"], ["check", "Cần xem"], ["sens", "Nhạy cảm"], ["basic", "Cơ bản"], ["none", "Không phải DLCN"]].map(([k, l]) => (
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
                  const needs = sens(c.nhom) || c.nhom === "pii_co_ban";
                  return (
                    <tr key={c.col} className={sens(c.nhom) && !d ? "needs" : undefined}>
                      <td><div className="num" style={{ fontWeight: 500 }}>{c.col}</div><div className="xs muted">001_init.sql dòng {c.line}</div></td>
                      <td><div style={{ fontWeight: 500, color: sens(c.nhom) ? "var(--color-cool)" : undefined }}>{label(c.nhom)}</div><div className="xs muted num">{basis(c.nhom)}</div></td>
                      <td><div className="num">{c.conf.toFixed(1)}</div><div className="xs muted">{c.conf >= 0.7 ? "khớp từ khoá" : "dưới ngưỡng"}</div></td>
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
                  const hit = SHP.columns.some((c) => c.nhom === k);
                  return (
                    <li key={k} style={{ display: "grid", gridTemplateColumns: "26px 1fr", gap: 8, padding: "7px 0", fontSize: 13.5, color: hit ? "var(--color-ink)" : "var(--color-muted)", fontWeight: hit ? 600 : 400 }}>
                      <span className="num">{d}</span><span>{t}{hit && <span className="chip chip--found" style={{ marginLeft: 8, minHeight: 20 }}>1 cột</span>}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
            <div className="note note--human">
              <h4>Vì sao đây là chỗ AI cần thiết</h4>
              Từ điển từ khoá không bắt được tên cột viết tắt kiểu <span className="num">tt_sk</span>, <span className="num">ghi_chu_bn</span>. Mỗi lần bạn bấm Đúng hoặc Sai được ghi lại làm số liệu cho ablation.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScreenLuatSu() {
  const [copied, setCopied] = useState(false);
  const question = "Khi người dùng tự nhập nội dung vào ô chat của ứng dụng chúng tôi vận hành, và nội dung đó được gửi tới nền tảng AI đặt ngoài lãnh thổ Việt Nam, hành vi này có thuộc trường hợp \"chủ thể dữ liệu tự chuyển dữ liệu của mình\" tại khoản 6 Điều 20 Luật 91/2025/QH15 hay không?";
  const copy = () => { navigator.clipboard && navigator.clipboard.writeText(question); setCopied(true); setTimeout(() => setCopied(false), 1800); };
  return (
    <div className="screen">
      <div className="wrap page">
        <Back />
        <div className="note note--plain row" style={{ marginBottom: 26, "--gap": "10px" }}>
          <Chip kind="line">Ví dụ trạng thái</Chip>
          <span className="small">Repo <span className="num">mini_repo</span> không rơi vào trạng thái này. Màn hình minh hoạ khi rule engine trả <span className="num">CAN_LUAT_SU</span> cho C1.</span>
        </div>
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
