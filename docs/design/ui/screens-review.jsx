// S6 Cổng duyệt (POST confirm) · S7 Hồ sơ nháp (ban_nhap_markdown của BE) · F Logic rule engine · S8 Ablation

function ScreenDuyet() {
  const { state, set } = useApp();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const r = state.result;
  if (!r) return <NeedStep what="kết quả phân tích" />;
  const k = r.ket_qua;
  const findings = GROUPS.filter(([g]) => ACTIVE.has(k[g].trang_thai)).map(([g, c]) => ({ g, c, x: k[g] }));
  const checked = state.approved;
  const toggle = (id) => set({ approved: { ...checked, [id]: !checked[id] } });
  const allRead = findings.every((f) => checked[f.c]);
  const canGo = state.reviewer.trim() && state.role && state.ack && allRead && !busy;

  async function confirm() {
    if (!canGo) return;
    setBusy(true); setErr(null);
    try {
      const draft = await API.confirm(r.session_id);
      set({ draft: { ...draft, reviewer: state.reviewer.trim(), role: state.role, at: new Date().toISOString() } });
      location.hash = "#/ho-so";
    } catch (x) { setErr(x); } finally { setBusy(false); }
  }

  return (
    <div className="screen">
      <div className="wrap page">
        <Back />
        <div className="page-head">
          <div>
            <h1>Cổng duyệt của người chịu trách nhiệm</h1>
            <p className="lede">Mở bằng chứng của từng phát hiện, đánh dấu đã đọc, rồi xác nhận. Bản nháp sinh từ kết luận mới nhất của phiên.</p>
          </div>
          <Chip kind={state.draft ? "ok" : "none"}>{state.draft ? "Đã sinh bản nháp" : "Chưa có hồ sơ nào được sinh ra"}</Chip>
        </div>
        <div className="grid-2" style={{ gap: 32 }}>
          <div className="sheet">
            <ul className="ruled" style={{ borderTop: 0 }}>
              {findings.length === 0 && <li style={{ padding: "18px 22px" }} className="small muted">Không có phát hiện nào cần duyệt: cả ba nhóm đều không thấy bằng chứng trong mã đã quét.</li>}
              {findings.map(({ g, c, x }) => (
                <li key={c} style={{ padding: "18px 22px" }}>
                  <div className="row" style={{ flexWrap: "nowrap", alignItems: "flex-start", "--gap": "14px" }}>
                    <label className="check" style={{ flex: 1 }}>
                      <input type="checkbox" checked={!!checked[c]} onChange={() => toggle(c)} />
                      <span>
                        <span className="row" style={{ "--gap": "8px" }}><Pin c={c} size="sm" /><b style={{ fontWeight: 600 }}>{g} · {x.ten}</b><Status s={x.trang_thai} /></span>
                        <span className="xs muted" style={{ display: "block", marginTop: 4 }}>{x.giai_thich}</span>
                        {x.can_cu && x.can_cu.length > 0 && <span className="num xs muted" style={{ display: "block", marginTop: 4 }}>{x.can_cu.map((cc) => cc.ma).join(", ")}</span>}
                        {x.trang_thai === "CAN_NGUOI_XAC_NHAN" && <span className="xs" style={{ display: "block", marginTop: 6, color: "var(--color-accent-text)" }}>Còn thiếu thông tin doanh nghiệp; sửa ở màn kết quả để chốt căn cứ.</span>}
                        {state.decisions[c] === "xac_nhan" && <span className="xs cool" style={{ display: "block", marginTop: 6 }}>Bạn đã xác nhận ở màn bằng chứng.</span>}
                        {state.decisions[c] === "bac_bo" && <span className="xs" style={{ display: "block", marginTop: 6, color: "var(--color-accent-text)" }}>Bạn đã bác bỏ ở màn bằng chứng. Bản nháp của backend vẫn dựa trên kết luận của rule engine.</span>}
                      </span>
                    </label>
                    <a className="small" href={x.trang_thai === "CAN_LUAT_SU" ? "#/luat-su" : "#/bang-chung/" + c}>Bằng chứng</a>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="stack" style={{ "--gap": "18px" }}>
            <div className="panel stack" style={{ "--gap": "14px" }}>
              <h2>Người chịu trách nhiệm</h2>
              <div className="field">
                <label htmlFor="ten">Họ và tên</label>
                <input id="ten" type="text" placeholder="[Tên người duyệt]" value={state.reviewer} onChange={(e) => set({ reviewer: e.target.value })} />
              </div>
              <div className="field">
                <label htmlFor="vaitro">Vai trò</label>
                <select id="vaitro" value={state.role} onChange={(e) => set({ role: e.target.value })}>
                  <option value="">Chọn vai trò</option>
                  <option>Chủ doanh nghiệp, người đại diện</option>
                  <option>Freelancer, agency bàn giao app</option>
                  <option>Tech lead</option>
                  <option>Cán bộ pháp chế</option>
                </select>
              </div>
              <label className="check small">
                <input type="checkbox" checked={state.ack} onChange={(e) => set({ ack: e.target.checked })} />
                <span>Tôi đã đọc bằng chứng cho từng phát hiện và chịu trách nhiệm về việc dùng hồ sơ nháp này.</span>
              </label>
              <p className="xs muted">Tên và vai trò chỉ hiện trên trang này, không gửi về backend.</p>
            </div>
            <div className="panel">
              <h3>Hệ thống sẽ không</h3>
              <ul className="ruled" style={{ marginTop: 10 }}>
                {["Tự gửi hồ sơ lên cơ quan chuyên trách", "Cấp chứng nhận", "Đưa ra ý kiến pháp lý thay luật sư"].map((t) => (
                  <li key={t} className="row small" style={{ "--gap": "10px", padding: "9px 0" }}><span aria-hidden="true" style={{ fontWeight: 700 }}>×</span>{t}</li>
                ))}
              </ul>
            </div>
            <ErrorNote err={err} />
          </div>
        </div>
      </div>
      <ActionBar>
        <span className="small muted">{canGo ? "Sẵn sàng xác nhận kết luận." : "Nút bật khi đã đánh dấu đọc mọi phát hiện, ghi tên, chọn vai trò và tích xác nhận."}</span>
        <button type="button" className="btn btn--primary" onClick={confirm} disabled={!canGo} aria-disabled={!canGo}>{busy ? "Đang sinh…" : "Xác nhận kết luận"}</button>
      </ActionBar>
    </div>
  );
}

function Blank({ children = "CẦN ĐIỀN" }) { return <span className="blank">[{children}]</span>; }

// Markdown tối giản của BE: "## tiêu đề", "- mục", đoạn văn; "__" là ô hệ thống không biết → ô cam
function inlineBlanks(text, key) {
  return text.split(/(__+)/).map((p, i) => /^__+$/.test(p) ? <Blank key={key + "-" + i} /> : p);
}
function Markdown({ text }) {
  const out = [];
  let list = [];
  const flush = () => { if (list.length) { out.push(<ul key={"u" + out.length}>{list}</ul>); list = []; } };
  text.split("\n").forEach((line, i) => {
    if (/^\s*-\s+/.test(line)) { list.push(<li key={i}>{inlineBlanks(line.replace(/^\s*-\s+/, ""), i)}</li>); return; }
    flush();
    if (/^#{1,3}\s/.test(line)) out.push(<h3 key={i}>{line.replace(/^#+\s*/, "")}</h3>);
    else if (line.trim()) out.push(<p key={i}>{inlineBlanks(line, i)}</p>);
  });
  flush();
  return <>{out}</>;
}

function ScreenHoSo() {
  const { state } = useApp();
  const d = state.draft;
  if (!d) return <NeedStep what="bản nháp" to={state.result ? "duyet" : "quet"} label={state.result ? "Về cổng duyệt" : "Quét mới"} />;
  const who = d.reviewer || "[Tên người duyệt]";
  const stamp = "Duyệt bởi: " + who + (d.role ? " (" + d.role + ")" : "") + " · " + d.at + "\nNguồn: " + srcLabel(state.scan) + " · chế độ " + (state.result && state.result.che_do) + "\n\n";
  const md = stamp + d.ban_nhap_markdown;
  const json = JSON.stringify({ nguon: state.scan && state.scan.nguon, ket_qua: state.result && state.result.ket_qua,
    ket_qua_da_xac_nhan: d.ket_qua_da_xac_nhan, nguoi_duyet: who, vai_tro: d.role, luc: d.at, luu_y: state.result && state.result.luu_y }, null, 2);
  const name = "ban-nhap-" + ((state.scan && state.scan.nguon && state.scan.nguon.ten) || "phien").replace(/[^\w.-]+/g, "_");
  return (
    <div className="screen">
      <div className="wrap page">
        <Back to="duyet" label="Cổng duyệt" />
        <div className="page-head">
          <div>
            <div className="meta"><span>duyệt bởi {who}</span>{d.role && <span>{d.role.toLowerCase()}</span>}<span>{srcLabel(state.scan)}</span></div>
            <h1>Hồ sơ nháp</h1>
          </div>
          <div className="row">
            <button type="button" className="btn btn--primary" onClick={() => API.download(name + ".md", md, "text/markdown;charset=utf-8")}>Tải bản nháp .md</button>
            <button type="button" className="btn" onClick={() => API.download(name + ".json", json, "application/json")}>Tải kết quả JSON</button>
          </div>
        </div>
        <div className="grid-2" style={{ gridTemplateColumns: "minmax(0, 8fr) minmax(0, 4fr)", gap: 32 }}>
          <div className="bench" style={{ padding: "36px 40px" }}>
            <article className="draft">
              <div className="doc-top"><Chip kind="draft">BẢN NHÁP · chưa được luật sư rà soát</Chip></div>
              <Markdown text={d.ban_nhap_markdown} />
              <p className="xs muted" style={{ marginTop: 14 }}>Sinh bởi backend từ kết luận đã xác nhận. Không tự gửi đi đâu.</p>
            </article>
          </div>
          <div className="stack" style={{ "--gap": "18px" }}>
            <div className="panel">
              <h3>Kết luận đã xác nhận</h3>
              <ul className="ruled" style={{ marginTop: 12 }}>
                {GROUPS.map(([g, c]) => (
                  <li key={g} className="row small" style={{ justifyContent: "space-between" }}>
                    <span className="row" style={{ "--gap": "8px" }}><Pin c={c} size="sm" />{g}</span>
                    <Status s={d.ket_qua_da_xac_nhan && d.ket_qua_da_xac_nhan[g]} />
                  </li>
                ))}
              </ul>
            </div>
            <div className="note note--human">
              <h4>Ô cam là ô hệ thống không biết</h4>
              Hệ thống chỉ điền những gì đọc được từ mã nguồn: loại dữ liệu, đích nhận, số dòng. Mục đích, thời gian lưu, hợp đồng với bên nhận đều để trống. Không điền hộ, không bịa.
            </div>
            <div className="note note--plain">
              <h4>Định dạng</h4>
              Bản nháp là markdown, đúng phạm vi spec §4. Chưa xuất <span className="num">.docx</span>.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Tree({ title, c, nodes }) {
  return (
    <div>
      <h2 className="row" style={{ fontSize: 18, letterSpacing: "-0.02em", "--gap": "10px", marginBottom: 14 }}><Pin c={c} />{title}</h2>
      <div className="tree">
        {nodes.map((n, i) => n.q ? <div key={i} className="q">{n.q}</div>
          : n.e ? <div key={i} className="edge" dangerouslySetInnerHTML={{ __html: n.e }} />
          : <div key={i} className={"out out--" + n.k}><b>{n.o}</b>{n.d}</div>)}
      </div>
    </div>
  );
}

function ScreenLogic() {
  return (
    <div className="screen">
      <div className="wrap page">
        <div className="page-head">
          <div>
            <div className="meta"><span>bước 5</span><span>codebase/rules.py</span><span>không gọi AI</span></div>
            <h1>Mỗi kết luận đi qua cây điều kiện viết tay</h1>
            <p className="lede">AI chỉ cấp hai thứ vào đây: nhãn phân loại cột kèm độ chắc, và cờ xác nhận hoặc bác bỏ từng đường đi. Mọi số điều, khoản, ngưỡng, mức phạt đọc từ bảng JSON.</p>
          </div>
        </div>
        <div className="bench">
          <div className="grid-3" style={{ gap: 28 }}>
            <Tree c="c1" title="C1 · Xuyên biên giới" nodes={[
              { q: "Có đường đi dữ liệu cá nhân tới dịch vụ ngoài lãnh thổ được xác nhận?" },
              { e: "<b>không</b> → KHONG_KICH_HOAT" },
              { q: "Nguồn của dữ liệu là hệ thống (cột trong database)?" },
              { e: "<b>có</b>" },
              { o: "KICH_HOAT", k: "found", d: "Luat91 D20.1, D20.2 · hạn 60 ngày · ND330 D56.1" },
              { e: "<b>không</b>: người dùng tự nhập hoặc chưa rõ nguồn" },
              { o: "CAN_LUAT_SU", k: "human", d: "Luat91 D20.6 · có thể thuộc trường hợp không phải đánh giá" },
            ]} />
            <Tree c="c2" title="C2 · Sự đồng ý" nodes={[
              { q: "Có ô đồng ý tích sẵn, hoặc câu coi im lặng là đồng ý?" },
              { e: "<b>có</b>" },
              { o: "KICH_HOAT_NANG", k: "found", d: "thêm Luat91 D9.4d (im lặng), ND356 D6.3 (tích sẵn)" },
              { e: "<b>không</b>" },
              { q: "Có cột dữ liệu cá nhân (độ chắc ≥ 0.7) mà chưa có bảng consent đủ 3 trường: người dùng, thời điểm, phiên bản chính sách?" },
              { e: "<b>có</b>" },
              { o: "KICH_HOAT", k: "found", d: "Luat91 D9.3 · ND356 D6" },
              { e: "<b>không</b>" },
              { o: "KHONG_KICH_HOAT", k: "none", d: "Có bảng nhật ký đồng ý đủ 3 trường, hoặc không có dữ liệu cá nhân" },
            ]} />
            <Tree c="c3" title="C3 · Miễn trừ" nodes={[
              { q: "Loại hình là doanh nghiệp lớn?" },
              { e: "<b>có</b> → KHONG_THUOC_DIEN_MIEN" },
              { q: "Loại hình hoặc số chủ thể lũy kế chưa rõ?" },
              { e: "<b>có</b>" },
              { o: "CAN_NGUOI_XAC_NHAN", k: "human", d: "Hỏi người dùng ở bước 1, không đoán từ code" },
              { e: "<b>không</b>" },
              { q: "Có cột nhạy cảm độ chắc ≥ 0.7, hoặc lũy kế ≥ 100.000 chủ thể?" },
              { e: "<b>có</b>" },
              { o: "MAT_MIEN_TRU", k: "found", d: "Điều 21, 22, khoản 2 Điều 33 phát sinh · Luat91 D38 · ND356 D41" },
              { e: "<b>không</b>, nhưng có cột chưa rõ nhóm → CAN_NGUOI_XAC_NHAN" },
              { o: "CON_MIEN_TRU", k: "ok", d: "theo loại hình: Luat91 D38.2 hoặc D38.3" },
            ]} />
          </div>
        </div>
        <div className="note note--human" style={{ marginTop: 24 }}>
          Hai thứ không bao giờ suy từ mã nguồn mà phải hỏi ở bước 1: loại hình tổ chức, số chủ thể lũy kế. Chọn "không rõ" thì rule engine trả <span className="num">CAN_NGUOI_XAC_NHAN</span> thay vì đoán.
        </div>
      </div>
    </div>
  );
}

function ScreenAblation() {
  const M = SHP.measured.ablation;
  const cell = (name, k) => (M && M[name] && M[name][k] != null ? <span className="num" style={{ fontSize: 16 }}>{M[name][k]}</span> : <span className="blank" style={{ background: "oklch(30% 0.03 60)", color: "oklch(85% 0.1 60)", boxShadow: "none" }}>đo</span>);
  return (
    <div className="screen" style={{ background: "var(--color-night)", color: "var(--color-night-ink)", minHeight: "calc(100vh - 65px)" }}>
      <div className="wrap page">
        <div className="meta" style={{ color: "var(--color-night-cool)" }}><span>slide 5</span><span>chỉ điền số đã đo</span></div>
        <h1 style={{ fontSize: "clamp(34px, 4vw, 56px)", maxWidth: 900 }}>AI cần ở đâu, rule engine cần ở đâu.</h1>
        <p style={{ marginTop: 14, fontSize: 18, color: "var(--color-night-muted)", maxWidth: 760 }}>
          Ba cấu hình chạy trên cùng bộ câu thử <span className="num">eval/benchmark.csv</span> ({SHP.benchmarkSize} câu, dựng từ {SHP.casesSize} case tự dán nhãn). Chuẩn "đạt" chốt ở CP2 trong <span className="num">metric_spec.yaml</span>.
        </p>

        <div className="table-box" style={{ marginTop: 40, borderTop: "1px solid var(--color-night-ink)" }}>
          <table className="table" style={{ color: "var(--color-night-ink)" }}>
            <thead>
              <tr>
                {["Chỉ số", "Chuẩn đạt", "A · chỉ rule", "B · chỉ LLM", "C · rule + LLM"].map((h, i) => (
                  <th key={h} style={{ color: "var(--color-night-muted)", borderColor: "var(--color-night-rule)", background: i === 4 ? "var(--color-night-2)" : undefined }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SHP.metrics.map((m) => (
                <tr key={m.name}>
                  <td style={{ borderColor: "var(--color-night-rule)" }}>
                    <div style={{ fontWeight: 600, fontSize: 15 }}>{m.label}</div>
                    <div className="num xs" style={{ color: "var(--color-night-muted)" }}>{m.name}{m.why && " · " + m.why}</div>
                  </td>
                  <td className="num small" style={{ borderColor: "var(--color-night-rule)", color: "var(--color-night-cool)" }}>{m.threshold}</td>
                  <td style={{ borderColor: "var(--color-night-rule)" }}>{cell(m.name, "A")}</td>
                  <td style={{ borderColor: "var(--color-night-rule)" }}>{cell(m.name, "B")}</td>
                  <td style={{ borderColor: "var(--color-night-rule)", background: "var(--color-night-2)" }}>{cell(m.name, "C")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14, marginTop: 32 }}>
          {[["Thời gian quét", "trung vị trên repo demo", SHP.measured.scanSeconds, "giây"], ["Chi phí mỗi lượt", "đọc từ nhật ký cổng AI", SHP.measured.costVnd, "đ"], ["So với làm tay", "n = 3, tự bấm giờ", SHP.measured.manualMinutes, "phút"]].map(([l, d, v, u]) => (
            <div key={l} className="stat">
              <div className="label">{l}</div>
              <div className="val">{v == null ? <NotMeasured night /> : <>{v} <small>{u}</small></>}</div>
              <div className="xs" style={{ color: "var(--color-night-muted)", marginTop: 4 }}>{d}</div>
            </div>
          ))}
        </div>
        <p className="xs" style={{ marginTop: 22, color: "var(--color-night-muted)" }}>
          Nhãn do nhóm tự dán, chưa có luật sư duyệt. Số lấy từ <span className="num">python run.py score eval/run-N.csv</span>; điền vào <span className="num">SHP.measured.ablation</span> trong <span className="num">data.js</span>, không gõ tay lên slide.
        </p>
      </div>
    </div>
  );
}

Object.assign(window, { ScreenDuyet, ScreenHoSo, ScreenLogic, ScreenAblation });
