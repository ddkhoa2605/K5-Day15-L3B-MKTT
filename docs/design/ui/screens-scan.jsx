// S0 Quét mới (POST /api/scan) · S1 Xem trước + gửi kiểm tra (POST analyze) · S2 Kết quả (+ POST business)

const MISSING = { loai_hinh: "loại hình tổ chức", so_chu_the_luy_ke: "số chủ thể lũy kế" };
const SOURCES = [["demo", "Repo demo"], ["github", "Link GitHub"], ["zip", "File .zip"], ["case", "JSON mô tả"]];

// Thông tin doanh nghiệp người dùng tự khai — BE không đoán từ code
function bizBody(state) {
  const body = { loai_hinh: state.loaiHinh };
  const n = String(state.soChuThe).trim();
  if (!state.soKhongRo && n !== "") body.so_chu_the_luy_ke = Number(n);
  return body;
}
function bizError(state) {
  if (state.soKhongRo) return null;
  const n = String(state.soChuThe).trim();
  if (n === "") return "Nhập số chủ thể lũy kế, hoặc chọn \"Không rõ\".";
  if (!/^\d+$/.test(n)) return "Số chủ thể phải là số nguyên ≥ 0.";
  return null;
}

function BizFields({ options, compact }) {
  const { state, set } = useApp();
  const list = (options && options.loai_hinh) || SHP.loaiHinh.map(([ma, ten]) => ({ ma, ten }));
  return (
    <div className={compact ? "row" : "stack"} style={compact ? { "--gap": "12px 20px", alignItems: "flex-end" } : { "--gap": "18px" }}>
      <div className="field" style={compact ? { minWidth: 240 } : undefined}>
        <label htmlFor="loai">Loại hình tổ chức</label>
        <select id="loai" value={state.loaiHinh} onChange={(e) => set({ loaiHinh: e.target.value })}>
          {list.map((o) => <option key={o.ma} value={o.ma}>{o.ten}</option>)}
        </select>
      </div>
      {compact ? (
        <div className="field" style={{ minWidth: 240 }}>
          <label htmlFor="sct">Số chủ thể dữ liệu đã xử lý, lũy kế</label>
          <input id="sct" className="num" type="text" inputMode="numeric" placeholder="Để trống nếu chưa rõ"
            value={state.soKhongRo ? "" : state.soChuThe} onChange={(e) => { const v = e.target.value.replace(/[.\s,]/g, ""); set({ soChuThe: v, soKhongRo: v === "" }); }} />
        </div>
      ) : (
        <fieldset style={{ border: 0, margin: 0, padding: 0 }}>
          <legend className="panel-label" style={{ marginBottom: 8 }}>Số chủ thể dữ liệu đã xử lý, tính lũy kế</legend>
          <div className="choices">
            {[[false, "Đã biết số"], [true, "Không rõ"]].map(([v, l]) => (
              <label key={l} className="choice">
                <input type="radio" name="sokhongro" checked={!!state.soKhongRo === v} onChange={() => set({ soKhongRo: v })} />{l}
              </label>
            ))}
          </div>
          <div className="field" style={{ marginTop: 10 }}>
            <label htmlFor="sct">Số chủ thể lũy kế</label>
            <input id="sct" className="num" type="text" inputMode="numeric" disabled={!!state.soKhongRo}
              placeholder={state.soKhongRo ? "Không rõ, rule engine sẽ hỏi lại" : "Ví dụ 4200"}
              value={state.soKhongRo ? "" : state.soChuThe} onChange={(e) => set({ soChuThe: e.target.value.replace(/[.\s,]/g, "") })} />
          </div>
          <p className="hint">Lũy kế tổng lượng đã xử lý, không phải người dùng đang hoạt động. Ngưỡng <span className="num">100.000</span> theo <span className="num">ND356 D41.2</span>.</p>
        </fieldset>
      )}
    </div>
  );
}

function ScreenQuet() {
  const { state, set } = useApp();
  const [repos, setRepos] = useState(null);
  const [options, setOptions] = useState(null);
  const [zip, setZip] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    API.demoRepos().then((d) => {
      setRepos(d.repos || []);
      if (!state.demoRepo && d.repos && d.repos.length) set({ demoRepo: d.repos[0].id });
    }).catch(() => setRepos([]));
    API.options().then(setOptions).catch(() => {});
  }, []);

  async function source() {
    if (state.nguon === "demo") {
      if (!state.demoRepo) throw new API.ApiError(400, { thong_bao: "Chưa chọn repo demo." });
      return { demo_repo: state.demoRepo };
    }
    if (state.nguon === "github") {
      if (!/^https:\/\/github\.com\/[^/\s]+\/[^/\s]+\/?$/.test(state.githubUrl.trim()))
        throw new API.ApiError(400, { thong_bao: "Link phải có dạng https://github.com/<owner>/<repo>." });
      return { github_url: state.githubUrl.trim() };
    }
    if (state.nguon === "zip") {
      if (!zip) throw new API.ApiError(400, { thong_bao: "Chưa chọn file .zip." });
      return { zip_base64: await API.readZip(zip), ten_file: zip.name };
    }
    let obj;
    try { obj = JSON.parse(state.caseText); } catch (e) { throw new API.ApiError(400, { thong_bao: "JSON không đọc được: " + e.message }); }
    return { case: obj && obj.case ? obj.case : obj };
  }

  async function submit(e) {
    e && e.preventDefault();
    const be = bizError(state);
    if (be) return setErr(new API.ApiError(400, { thong_bao: be }));
    setBusy(true); setErr(null);
    try {
      const body = { ...(await source()), ...bizBody(state), che_do: state.mode };
      const scan = await API.scan(body);
      set({ scan, result: null, draft: null, decisions: {}, colDecisions: {}, approved: {}, ack: false });
      location.hash = "#/dang-quet";
    } catch (x) { setErr(x); } finally { setBusy(false); }
  }

  return (
    <div className="screen">
      <div className="wrap page" style={{ paddingBottom: 48 }}>
        <div className="grid-2r" style={{ gap: 56, alignItems: "stretch" }}>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <h1 style={{ fontSize: "clamp(36px, 4.2vw, 58px)" }}>Nghĩa vụ dữ liệu cá nhân, chỉ ra tới từng dòng code.</h1>
            <p style={{ marginTop: 18, fontSize: 18, color: "var(--color-ink-2)", maxWidth: 520 }}>
              Đưa repo Next.js + Supabase trước khi bàn giao. Hệ thống chỉ đọc mã nguồn, không truy cập app đang chạy.
            </p>
            <form className="stack" style={{ "--gap": "14px", marginTop: "auto", paddingTop: 30, maxWidth: 540 }} onSubmit={submit}>
              <div className="seg" role="group" aria-label="Nguồn">
                {SOURCES.map(([k, l]) => <button key={k} type="button" aria-pressed={state.nguon === k} onClick={() => set({ nguon: k })}>{l}</button>)}
              </div>
              {state.nguon === "demo" && (
                <div className="field">
                  <label htmlFor="demo">Repo demo trên máy backend</label>
                  <select id="demo" value={state.demoRepo} onChange={(e) => set({ demoRepo: e.target.value })} disabled={!repos || !repos.length}>
                    {repos === null && <option>Đang tải…</option>}
                    {repos && !repos.length && <option value="">Không có repo demo (hoặc chưa nối backend)</option>}
                    {(repos || []).map((r) => <option key={r.id} value={r.id}>{r.id} · {r.mo_ta}</option>)}
                  </select>
                </div>
              )}
              {state.nguon === "github" && (
                <div className="field">
                  <label htmlFor="gh">Link repo GitHub công khai</label>
                  <input id="gh" className="num" type="url" placeholder="https://github.com/owner/repo" value={state.githubUrl} onChange={(e) => set({ githubUrl: e.target.value })} />
                  <p className="hint">Backend tải bản zip của nhánh mặc định (cần mạng, tối đa 30 giây).</p>
                </div>
              )}
              {state.nguon === "zip" && (
                <div className="field">
                  <label htmlFor="zip">File .zip mã nguồn (≤ 20 MB)</label>
                  <input id="zip" type="file" accept=".zip,application/zip" onChange={(e) => setZip(e.target.files[0] || null)} />
                  <p className="hint">Chỉ đọc <span className="num">.ts .tsx .js .jsx .sql .json</span>…, bỏ <span className="num">node_modules</span>, <span className="num">.git</span>.</p>
                </div>
              )}
              {state.nguon === "case" && (
                <div className="field">
                  <label htmlFor="case">Một case JSON (mo_ta, schema, code)</label>
                  <textarea id="case" className="num" rows="6" value={state.caseText} onChange={(e) => set({ caseText: e.target.value })}
                    placeholder='{"mo_ta": "...", "schema": ["users(id, email)"], "code": [{"file": "a.ts", "line": 3, "text": "..."}]}' />
                </div>
              )}
              <ErrorNote err={err} />
            </form>
          </div>

          <div className="bench" style={{ display: "flex" }}>
            <div className="sheet" style={{ padding: "22px 24px", flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                <h2 style={{ fontSize: 20, letterSpacing: "-0.02em" }}>Hai điều mã nguồn không nói được</h2>
                <Chip kind="human">Bạn trả lời</Chip>
              </div>
              <p className="small muted" style={{ marginBottom: 18 }}>Quyết định bạn còn miễn trừ Điều 21, 22 và khoản 2 Điều 33 hay không. Hệ thống không đoán từ code; sửa được sau ở màn kết quả mà không gọi lại AI.</p>
              <BizFields options={options} />
            </div>
          </div>
        </div>

        <div className="grid-3" style={{ marginTop: 56 }}>
          <div className="panel" style={{ gridColumn: "span 2" }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h2>Gửi gì ra ngoài</h2>
              <div className="seg" role="group" aria-label="Chế độ">
                {["rule", "hybrid"].map((m) => (
                  <button key={m} type="button" aria-pressed={state.mode === m} onClick={() => set({ mode: m })}>{m}</button>
                ))}
              </div>
            </div>
            <p className="small muted" style={{ margin: "6px 0 16px" }}>
              {state.mode === "rule" ? "Chế độ rule chỉ dùng luật viết tay: không gọi model, không gửi gì." : "Chế độ hybrid gọi model AI đặt ở nước ngoài. Bước sau hiện đúng danh sách sẽ gửi, trước khi bạn bấm gửi."}
            </p>
            <ul className="ruled">
              {[
                [state.mode === "hybrid", "Mô tả app, tên bảng và tên cột trong schema"],
                [state.mode === "hybrid", "Đoạn code quanh lời gọi ra ngoài (đã lọc secret)"],
                [false, "Giá trị thật trong bảng dữ liệu"],
                [false, "Toàn bộ repo"],
                [false, "Secret, API key (thay bằng [REDACTED] trước khi gửi)"],
              ].map(([sent, t], i) => (
                <li key={i} className="row" style={{ "--gap": "14px", padding: "11px 0" }}>
                  <span className={"chip " + (sent ? "chip--found" : "chip--none")} style={{ minWidth: 64, justifyContent: "center" }}>{sent ? "Gửi" : "Không"}</span>
                  <span style={{ fontSize: 15 }}>{t}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="panel">
            <h2>Ba nhóm kiểm tra</h2>
            <ul className="ruled" style={{ marginTop: 14 }}>
              {[["c1", "C1", "Chuyển dữ liệu xuyên biên giới", "Luat91 D20"], ["c2", "C2", "Xin và lưu sự đồng ý", "Luat91 D9 · ND356 D6"], ["c3", "C3", "Mất miễn trừ", "Luat91 D38 · ND356 D41"]].map(([c, k, t, law]) => (
                <li key={c} style={{ display: "grid", gridTemplateColumns: "22px 1fr", gap: "2px 10px" }}>
                  <span style={{ paddingTop: 6 }}><Pin c={c} /></span>
                  <span style={{ fontWeight: 500 }}>{k} · {t}</span>
                  <span className="num xs muted" style={{ gridColumn: 2 }}>{law}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="note note--plain" style={{ marginTop: 22 }}>
          Hệ thống chỉ ra nghĩa vụ nào đã phát sinh và dòng code nào làm nó phát sinh. Không đưa ra ý kiến pháp lý, không cấp chứng nhận, không gửi gì cho cơ quan nhà nước.
        </div>
      </div>
      <ActionBar>
        <span className="small muted">Bước này chỉ quét tĩnh, chưa gọi AI.</span>
        <button type="button" className="btn btn--primary" onClick={submit} disabled={busy} aria-disabled={busy}>{busy ? "Đang quét…" : "Quét mã nguồn"}</button>
      </ActionBar>
    </div>
  );
}

const SCAN_STEPS = [
  { t: "Đọc schema và cấu hình", d: "scanner.py · không gọi AI", ai: false, static: true },
  { t: "Tìm lời gọi ra ngoài và cách xin đồng ý", d: "scanner.py · không gọi AI", ai: false, static: true },
  { t: "AI phân loại tên cột", d: "classify.py · model nhỏ", ai: true },
  { t: "AI kiểm chứng đường đi dữ liệu", d: "verify.py · model lớn · xác nhận hoặc bác bỏ", ai: true },
  { t: "Rule engine ra kết luận", d: "rules.py · không gọi AI · nơi duy nhất tạo kết luận pháp lý", ai: false },
];

function SendList({ title, part }) {
  if (!part) return null;
  return (
    <div style={{ marginTop: 14 }}>
      <div className="panel-label" style={{ color: "var(--color-night-cool)" }}>{title} · <span className="num">{part.model}</span></div>
      <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
        {(part.noi_dung || []).map((t, i) => <li key={i} className="small">{t}</li>)}
      </ul>
      {(part.doan_code || []).map((d, i) => (
        <pre key={i} className="num xs" style={{ whiteSpace: "pre-wrap", margin: "8px 0 0", padding: 10, background: "var(--color-night-2)", borderRadius: 6 }}>
          {d.file}:{d.tu_dong}-{d.den_dong}{"\n"}{d.text}
        </pre>
      ))}
      {part.kem_ten_cot_ca_nhan && <p className="xs" style={{ marginTop: 6, color: "var(--color-night-muted)" }}>Kèm: {part.kem_ten_cot_ca_nhan}</p>}
    </div>
  );
}

function ScreenDangQuet() {
  const { state, set } = useApp();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const scan = state.scan;
  if (!scan) return <NeedStep />;
  const rule = scan.che_do === "rule";
  const sg = scan.se_gui_ra_ngoai || {};
  const done = !!(state.result && state.result.session_id === scan.session_id);
  const stepState = (s) => s.static ? "done" : done ? "done" : busy ? "now" : "wait";

  async function analyze() {
    if (busy) return;
    setBusy(true); setErr(null);
    try {
      const result = await API.analyze(scan.session_id);
      set({ result });
      location.hash = "#/ket-qua";
    } catch (x) { setErr(x); } finally { setBusy(false); }
  }

  const tk = scan.thong_ke || {};
  return (
    <div className="screen">
      <div className="wrap page">
        <div className="page-head">
          <div>
            <div className="meta"><span>{srcLabel(scan)}</span><span>chế độ {scan.che_do}</span></div>
            <h1>{done ? "Đã phân tích xong." : "Quét tĩnh xong. Xem trước những gì sẽ gửi đi."}</h1>
            <p className="lede">{tk.so_file} file · {tk.so_cot} cột · {tk.so_loi_goi_ra_ngoai} lời gọi ra ngoài. Chưa có gì được gửi cho model.</p>
          </div>
        </div>

        <div className="grid-2r" style={{ gap: 40 }}>
          <div className="stack" style={{ "--gap": "24px" }}>
            <ol className="timeline">
              {SCAN_STEPS.map((s, i) => {
                const skipped = rule && s.ai;
                const cls = skipped ? "done" : stepState(s);
                return (
                  <li key={i} className={cls}>
                    <span className="dot">{cls === "done" ? "✓" : i + 1}</span>
                    <div>
                      <h3>
                        {s.t}
                        {s.ai && <Chip kind={skipped ? "none" : "human"}>{skipped ? "bỏ qua" : "AI"}</Chip>}
                        {cls === "now" && !skipped && <span className="chip chip--line pulse">đang chạy</span>}
                      </h3>
                      <p>{s.d}</p>
                    </div>
                  </li>
                );
              })}
            </ol>

            <div className="panel">
              <h3>Quét tĩnh tìm thấy</h3>
              <ul className="ruled" style={{ marginTop: 10 }}>
                {(scan.loi_goi_ra_ngoai || []).map((l, i) => (
                  <li key={"s" + i} className="small" style={{ padding: "8px 0" }}>
                    <span className="num">{l.file}:{l.line}</span> → <span className="num">{l.dich}</span> <Chip kind="line">{l.loai}</Chip>
                  </li>
                ))}
                {(scan.dong_y && scan.dong_y.tich_san || []).map((d, i) => (
                  <li key={"t" + i} className="small" style={{ padding: "8px 0" }}><span className="num">{d.file}:{d.line}</span> · ô đồng ý tích sẵn</li>
                ))}
                {(scan.dong_y && scan.dong_y.im_lang_dong_y || []).map((d, i) => (
                  <li key={"i" + i} className="small" style={{ padding: "8px 0" }}><span className="num">{d.file}:{d.line}</span> · câu coi im lặng là đồng ý</li>
                ))}
                <li className="small" style={{ padding: "8px 0" }}>
                  Bảng nhật ký đồng ý: {scan.dong_y && scan.dong_y.bang ? <span className="num">{scan.dong_y.bang}</span> : "không thấy"}
                  {scan.dong_y && scan.dong_y.bang && (scan.dong_y.du_3_truong ? " · đủ 3 trường" : " · chưa đủ 3 trường")}
                </li>
              </ul>
              {(scan.canh_bao || []).map((c, i) => <p key={i} className="xs" style={{ marginTop: 8, color: "var(--color-accent-text)" }}>{c}</p>)}
            </div>
          </div>

          <div className="night" style={{ padding: 22 }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
              <h2 style={{ fontSize: 20, letterSpacing: "-0.02em" }}>Sẽ gửi cho model AI</h2>
              <span className="xs muted">toàn bộ nội dung <span className="num">analyze</span> sẽ gửi</span>
            </div>
            {!sg.model_phan_loai && !sg.model_kiem_chung && <p className="small" style={{ marginTop: 12 }}>Không gửi gì.</p>}
            <SendList title="Model phân loại" part={sg.model_phan_loai} />
            <SendList title="Model kiểm chứng" part={sg.model_kiem_chung} />
            <p className="xs" style={{ marginTop: 16, color: "var(--color-night-muted)" }}>{sg.khong_gui}</p>
            {done && state.result.su_dung && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10, marginTop: 16 }}>
                {[["Lượt gọi model", state.result.su_dung.so_lan_goi_model], ["Token vào", state.result.su_dung.token_vao], ["Token ra", state.result.su_dung.token_ra]].map(([l, v]) => (
                  <div key={l} className="stat"><div className="label">{l}</div><div className="val">{v}</div></div>
                ))}
              </div>
            )}
          </div>
        </div>
        <ErrorNote err={err} />
      </div>
      <ActionBar>
        <span className="small muted">{busy ? (rule ? "Rule engine đang chạy…" : "Đang gọi model, thường 5–15 giây…") : rule ? "Chế độ rule: không gửi gì ra ngoài." : "Bấm gửi nghĩa là đồng ý gửi đúng danh sách bên phải."}</span>
        {done
          ? <a className="btn btn--primary" href="#/ket-qua">Xem kết quả</a>
          : <button type="button" className="btn btn--primary" onClick={analyze} disabled={busy} aria-disabled={busy}>{busy ? "Đang kiểm tra…" : rule ? "Chạy kiểm tra" : "Gửi kiểm tra"}</button>}
      </ActionBar>
    </div>
  );
}

function ScreenKetQua() {
  const { state, set } = useApp();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const r = state.result;
  if (!r) return <NeedStep what="kết quả phân tích" to={state.scan ? "dang-quet" : "quet"} label={state.scan ? "Về bước xem trước" : "Quét mới"} />;
  const k = r.ket_qua;
  const kinds = GROUPS.map(([g]) => (STATUS[k[g].trang_thai] || [, "none"])[1]);
  const found = kinds.filter((x) => x === "found").length;
  const human = kinds.filter((x) => x === "human").length;

  async function update() {
    const be = bizError(state);
    if (be) return setErr(new API.ApiError(400, { thong_bao: be }));
    setBusy(true); setErr(null);
    try { set({ result: await API.business(r.session_id, bizBody(state)), draft: null }); }
    catch (x) { setErr(x); } finally { setBusy(false); }
  }

  return (
    <div className="screen">
      <div className="wrap page">
        <div className="page-head">
          <div>
            <div className="meta">
              <span>{srcLabel(state.scan)}</span><span>chế độ {r.che_do}</span>
              <span>đã gửi ra ngoài: {r.da_gui_ra_ngoai && r.da_gui_ra_ngoai.length ? r.da_gui_ra_ngoai.length + " mục" : "không gửi gì"}</span>
              {r.su_dung && <span>{r.su_dung.so_lan_goi_model} lượt gọi model · {r.su_dung.token_vao + r.su_dung.token_ra} token</span>}
            </div>
            <h1>{found ? found + " nghĩa vụ đã phát sinh" : "Không thấy nghĩa vụ nào phát sinh trong mã đã quét"}{human ? ", " + human + " điểm chờ người xác nhận." : "."}</h1>
            <p className="lede">Đây là danh sách nghĩa vụ đã phát sinh, không phải ý kiến pháp lý. Mỗi dòng có bằng chứng trong code và điều luật làm căn cứ.</p>
          </div>
        </div>

        <div className={"note row " + (r.thieu_thong_tin && r.thieu_thong_tin.length ? "note--human" : "note--plain")} style={{ marginBottom: 28, "--gap": "16px 28px", justifyContent: "space-between", alignItems: "flex-end" }}>
          <div style={{ flex: "1 1 260px" }}>
            <h4>{r.thieu_thong_tin && r.thieu_thong_tin.length ? "Còn thiếu: " + r.thieu_thong_tin.map((t) => MISSING[t] || t).join(", ") : "Thông tin doanh nghiệp"}</h4>
            Sửa ở đây chỉ chạy lại rule engine, không gọi lại AI.
          </div>
          <BizFields compact />
          <button type="button" className="btn btn--primary btn--sm" onClick={update} disabled={busy}>{busy ? "Đang cập nhật…" : "Cập nhật kết luận"}</button>
        </div>
        <ErrorNote err={err} />

        <div className="bench">
          <div className="grid-3">
            {GROUPS.map(([g, c]) => {
              const x = k[g];
              const first = x.bang_chung && x.bang_chung[0];
              const cells = [["Giải thích", x.giai_thich, { wide: true, text: true }],
                             ["Căn cứ", x.can_cu && x.can_cu.length ? x.can_cu.map((cc) => cc.ma).join(", ") : "—", { mono: true, wide: true }]];
              if (x.han_chot) cells.push(["Hạn", x.han_chot, { wide: true }]);
              if (x.nhom_nhay_cam && x.nhom_nhay_cam.length) cells.push(["Nhóm nhạy cảm", x.nhom_nhay_cam.join(", "), { mono: true, wide: true }]);
              if (x.muc_phat) cells.push(["Mức phạt tham khảo", x.muc_phat, { wide: true, text: true }]);
              return (
                <Entry key={g} c={c} kind={g} where={first ? first.file.split("/").pop() + ":" + first.line : null} title={x.ten} cells={cells}
                  foot={<><Status s={x.trang_thai} />
                    {x.trang_thai === "CAN_LUAT_SU" ? <a className="btn btn--sm" href="#/luat-su">Vì sao cần luật sư</a>
                      : <a className="btn btn--sm" href={"#/bang-chung/" + c}>Bằng chứng ({(x.bang_chung || []).length})</a>}</>} />
              );
            })}
          </div>
        </div>
        {(r.canh_bao || []).map((c, i) => <p key={i} className="small" style={{ marginTop: 12, color: "var(--color-accent-text)" }}>{c}</p>)}
        <div className="note note--plain" style={{ marginTop: 22 }}>{r.luu_y} <a href="#/phan-loai">Xem toàn bộ cột đã quét</a></div>
      </div>
      <ActionBar>
        <span className="small muted">Gợi ý để người chịu trách nhiệm xác nhận, không phải ý kiến pháp lý.</span>
        <a className="btn btn--primary" href="#/duyet">Sang cổng duyệt</a>
      </ActionBar>
    </div>
  );
}

Object.assign(window, { ScreenQuet, ScreenDangQuet, ScreenKetQua, bizBody });
