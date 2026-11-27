// S6 Cổng duyệt · S7 Hồ sơ nháp · F Logic rule engine · S8 Ablation

const FINDINGS = [
  { id: "c1", c: "c1", t: "C1 · users.email → OpenAI, route.ts dòng 10", s: "Luat91 D20.1, D20.2 · hạn 60 ngày", link: "#/bang-chung/c1" },
  { id: "c2", c: "c2", t: "C2 · Ô đồng ý tích sẵn và im lặng là đồng ý, page.tsx dòng 5, 8", s: "Luat91 D9.3, D9.4d · ND356 D6, D6.3", link: "#/bang-chung/c2" },
  { id: "c3", c: "c3", t: "C3 · bookings.vi_tri_gan_nhat là dữ liệu vị trí", s: "ND356 D4h · không còn miễn trừ", link: "#/phan-loai" },
];

function ScreenDuyet() {
  const { state, set } = useApp();
  const c3 = c3Status(state.loaiHinh, state.luyKe);
  const checked = state.approved;
  const toggle = (id) => set({ approved: { ...checked, [id]: !checked[id] } });
  const canGo = state.reviewer.trim() && state.role && state.ack && Object.values(checked).some(Boolean);
  return (
    <div className="screen">
      <div className="wrap page">
        <Back />
        <div className="page-head">
          <div>
            <h1>Cổng duyệt của người chịu trách nhiệm</h1>
            <p className="lede">Chỉ phát hiện bạn đánh dấu mới đi vào hồ sơ nháp. Mở bằng chứng trước khi quyết định.</p>
          </div>
          <Chip kind="none">Chưa có hồ sơ nào được sinh ra</Chip>
        </div>
        <div className="grid-2" style={{ gap: 32 }}>
          <div className="sheet">
            <ul className="ruled" style={{ borderTop: 0 }}>
              {FINDINGS.map((f) => {
                const blocked = f.id === "c3" && c3 === "CAN_NGUOI_XAC_NHAN";
                return (
                  <li key={f.id} style={{ padding: "18px 22px" }}>
                    <div className="row" style={{ flexWrap: "nowrap", alignItems: "flex-start", "--gap": "14px" }}>
                      <label className="check" style={{ flex: 1 }}>
                        <input type="checkbox" checked={!!checked[f.id] && !blocked} disabled={blocked} onChange={() => toggle(f.id)} />
                        <span>
                          <span className="row" style={{ "--gap": "8px" }}><Pin c={f.c} size="sm" /><b style={{ fontWeight: 600 }}>{f.t}</b></span>
                          <span className="num xs muted" style={{ display: "block", marginTop: 4 }}>{f.s}</span>
                          {blocked && <span className="xs" style={{ display: "block", marginTop: 6, color: "var(--color-accent-text)" }}>Chưa duyệt được: cần chốt loại hình ở bước 1.</span>}
                          {state.decisions[f.id] === "xac_nhan" && <span className="xs cool" style={{ display: "block", marginTop: 6 }}>Bạn đã xác nhận ở màn bằng chứng.</span>}
                        </span>
                      </label>
                      <a className="small" href={blocked ? "#/quet" : f.link}>{blocked ? "Chốt loại hình" : "Bằng chứng"}</a>
                    </div>
                  </li>
                );
              })}
              <li style={{ padding: "18px 22px", background: "color-mix(in oklab, var(--color-accent-soft) 40%, transparent)" }}>
                <label className="check" style={{ opacity: .7 }}>
                  <input type="checkbox" disabled />
                  <span><b style={{ fontWeight: 600 }}>Ví dụ: C1 · đường đi chữ người dùng nhập, cần luật sư</b>
                    <span className="xs muted" style={{ display: "block", marginTop: 4 }}>Không xác nhận được. Ghi vào hồ sơ như mục chờ. <a href="#/luat-su">Xem vì sao</a></span></span>
                </label>
              </li>
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
                <span>Tôi đã đọc bằng chứng cho từng phát hiện đã chọn và chịu trách nhiệm về việc dùng hồ sơ nháp này.</span>
              </label>
            </div>
            <div className="panel">
              <h3>Hệ thống sẽ không</h3>
              <ul className="ruled" style={{ marginTop: 10 }}>
                {["Tự gửi hồ sơ lên cơ quan chuyên trách", "Cấp chứng nhận tuân thủ", "Kết luận bạn đã vi phạm"].map((t) => (
                  <li key={t} className="row small" style={{ "--gap": "10px", padding: "9px 0" }}><span aria-hidden="true" style={{ fontWeight: 700 }}>×</span>{t}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
      <ActionBar>
        <span className="small muted">{canGo ? "Sẵn sàng sinh bản nháp." : "Nút bật khi đã chọn ít nhất một phát hiện, ghi tên, chọn vai trò và tích xác nhận."}</span>
        <a className="btn btn--primary" href={canGo ? "#/ho-so" : undefined} aria-disabled={!canGo} onClick={(e) => { if (!canGo) e.preventDefault(); }}>Sinh hồ sơ nháp</a>
      </ActionBar>
    </div>
  );
}

function Blank({ children = "CẦN ĐIỀN" }) { return <span className="blank">[{children}]</span>; }

function ScreenHoSo() {
  const { state } = useApp();
  const c3 = c3Status(state.loaiHinh, state.luyKe);
  const who = state.reviewer.trim() || "[Tên người duyệt]";
  return (
    <div className="screen">
      <div className="wrap page">
        <Back to="duyet" label="Cổng duyệt" />
        <div className="page-head">
          <div>
            <div className="meta"><span>duyệt bởi {who}</span>{state.role && <span>{state.role.toLowerCase()}</span>}</div>
            <h1>Hồ sơ nháp</h1>
          </div>
          <div className="row">
            <button type="button" className="btn btn--primary">Tải bản nháp .md</button>
            <button type="button" className="btn">Tải kết quả JSON</button>
          </div>
        </div>
        <div className="grid-2" style={{ gridTemplateColumns: "minmax(0, 8fr) minmax(0, 4fr)", gap: 32 }}>
          <div className="bench" style={{ padding: "36px 40px" }}>
            <article className="draft">
              <div className="doc-top">
                <Chip kind="draft">Bản nháp, chưa được luật sư rà soát</Chip>
                <h2>Hồ sơ đánh giá tác động<br />chuyển dữ liệu cá nhân xuyên biên giới</h2>
                <p className="small muted" style={{ marginTop: 6 }}>Căn cứ <span className="num">Luat91 D20.1, Luat91 D20.2</span></p>
              </div>
              <section>
                <h3>I. Thông tin bên chuyển dữ liệu</h3>
                <dl><dt>Tên tổ chức</dt><dd><Blank /></dd><dt>Mã số thuế</dt><dd><Blank /></dd><dt>Người duyệt bản nháp</dt><dd>{who}</dd></dl>
              </section>
              <section>
                <h3>II. Mô tả hoạt động chuyển</h3>
                <dl>
                  <dt>Dòng chuyển</dt><dd><span className="num">app/api/chat/route.ts:10</span> → <span className="num">chat.completions.create</span></dd>
                  <dt>Trường dữ liệu</dt><dd><span className="num">users.email</span> (dữ liệu cá nhân cơ bản)</dd>
                  <dt>Mục đích chuyển</dt><dd><Blank>CẦN ĐIỀN · hệ thống không biết mục đích kinh doanh</Blank></dd>
                  <dt>Bên nhận, quốc gia</dt><dd><Blank /></dd>
                </dl>
              </section>
              <section>
                <h3>III. Biện pháp bảo vệ</h3>
                <Blank>CẦN ĐIỀN · đính kèm thoả thuận xử lý dữ liệu với bên nhận</Blank>
              </section>
              <section style={{ borderBottom: "2px solid var(--color-ink)" }}>
                <h3>IV. Hạn gửi</h3>
                <p><span className="num">60 ngày</span> kể từ lần chuyển dữ liệu đầu tiên. Gửi 01 bản chính cho cơ quan chuyên trách.</p>
              </section>
              <p className="xs muted" style={{ marginTop: 14 }}>Sinh từ lượt quét <span className="num">{state.repo}</span> · chế độ {state.mode}. Không tự gửi đi đâu.</p>
            </article>
          </div>
          <div className="stack" style={{ "--gap": "18px" }}>
            <div className="panel">
              <h3>Hồ sơ gồm</h3>
              <ul className="ruled" style={{ marginTop: 12 }}>
                <li className="row small" style={{ justifyContent: "space-between" }}><span>Hồ sơ chuyển dữ liệu xuyên biên giới (C1)</span><Chip kind="ok">Sinh được</Chip></li>
                <li className="row small" style={{ justifyContent: "space-between" }}><span>Sửa cách xin đồng ý (C2)</span><Chip kind="found">Việc cần làm</Chip></li>
                <li className="row small" style={{ justifyContent: "space-between" }}><span>Hồ sơ đánh giá tác động xử lý, Điều 21 (C3)</span>{c3 === "CAN_NGUOI_XAC_NHAN" ? <Chip kind="human">Chờ chốt loại hình</Chip> : <Chip kind="found">Phát sinh</Chip>}</li>
                <li className="row small" style={{ justifyContent: "space-between" }}><span>Phát hiện chờ luật sư</span><span className="num">0</span></li>
              </ul>
            </div>
            <div className="note note--human">
              <h4>Ô cam là ô hệ thống không biết</h4>
              Hệ thống chỉ điền những gì đọc được từ mã nguồn: loại dữ liệu, đích nhận, số dòng. Tên tổ chức, mục đích, hợp đồng, rủi ro đều để trống. Không điền hộ, không bịa.
            </div>
            <div className="note note--plain">
              <h4>Định dạng</h4>
              Bản nháp là markdown, đúng phạm vi spec §4. Chưa xuất <span className="num">.docx</span> trong 48 giờ.
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
