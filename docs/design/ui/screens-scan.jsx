// S0 Quét mới · S1 Đang quét + cổng AI · S2 Kết quả tổng quan

function ScreenQuet() {
  const { state, set } = useApp();
  return (
    <div className="screen">
      <div className="wrap page" style={{ paddingBottom: 48 }}>
        <div className="grid-2r" style={{ gap: 56, alignItems: "center" }}>
          <div>
            <h1 style={{ fontSize: "clamp(36px, 4.2vw, 58px)" }}>Nghĩa vụ dữ liệu cá nhân, chỉ ra tới từng dòng code.</h1>
            <p style={{ marginTop: 18, fontSize: 18, color: "var(--color-ink-2)", maxWidth: 520 }}>
              Đưa repo Next.js + Supabase trước khi bàn giao. Hệ thống chỉ đọc mã nguồn, không truy cập app đang chạy.
            </p>
            <form className="stack" style={{ "--gap": "12px", marginTop: 30, maxWidth: 540 }} onSubmit={(e) => { e.preventDefault(); location.hash = "#/dang-quet"; }}>
              <div className="field">
                <label htmlFor="repo">Đường dẫn repo</label>
                <input id="repo" className="num" type="text" value={state.repo} onChange={(e) => set({ repo: e.target.value })} />
              </div>
              <p className="hint" style={{ marginTop: 0 }}>Thư mục trên máy (<span className="num">repo:…</span>) hoặc một dòng JSON mô tả hệ thống.</p>
            </form>
          </div>

          <div className="bench">
            <div className="sheet" style={{ padding: "22px 24px" }}>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                <h2 style={{ fontSize: 20, letterSpacing: "-0.02em" }}>Ba điều mã nguồn không nói được</h2>
                <Chip kind="human">Bạn trả lời</Chip>
              </div>
              <p className="small muted" style={{ marginBottom: 18 }}>Quyết định bạn còn miễn trừ Điều 21, 22 và khoản 2 Điều 33 hay không. Hệ thống không đoán từ code.</p>

              <div className="stack" style={{ "--gap": "18px" }}>
                <div className="field">
                  <label htmlFor="loai">Loại hình tổ chức</label>
                  <select id="loai" value={state.loaiHinh} onChange={(e) => set({ loaiHinh: e.target.value })}>
                    {SHP.loaiHinh.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
                <fieldset style={{ border: 0, margin: 0, padding: 0 }}>
                  <legend className="panel-label" style={{ marginBottom: 8 }}>Số chủ thể dữ liệu đã xử lý, tính lũy kế</legend>
                  <div className="choices">
                    {[["duoi", "Dưới 100.000"], ["tren", "Từ 100.000 trở lên"], ["khong_ro", "Không rõ"]].map(([v, l]) => (
                      <label key={v} className="choice">
                        <input type="radio" name="luyke" checked={state.luyKe === v} onChange={() => set({ luyKe: v })} />{l}
                      </label>
                    ))}
                  </div>
                  <p className="hint">Lũy kế tổng lượng đã xử lý, không phải người dùng đang hoạt động. Ngưỡng <span className="num">100.000</span> theo <span className="num">ND356 D41.2</span>.</p>
                </fieldset>
              </div>
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
              {state.mode === "rule" ? "Chế độ rule chỉ dùng luật viết tay: không gọi model, không gửi gì." : "Chế độ hybrid gọi model AI đặt ở nước ngoài. Đây là toàn bộ những gì rời khỏi máy bạn."}
            </p>
            <ul className="ruled">
              {[
                [state.mode === "hybrid", "Tên bảng, tên cột trong schema"],
                [state.mode === "hybrid", "Đoạn code ±5 dòng quanh đường đi dữ liệu"],
                [false, "Giá trị thật trong bảng dữ liệu"],
                [false, "Toàn bộ repo"],
                [false, "Secret, API key, biến môi trường (lọc trước khi gửi)"],
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
          Hệ thống chỉ ra nghĩa vụ nào đã phát sinh và dòng code nào làm nó phát sinh. Không kết luận vi phạm, không cấp chứng nhận tuân thủ, không gửi gì cho cơ quan nhà nước.
        </div>
      </div>
      <ActionBar>
        <span className="small muted">Chi phí mỗi lượt quét: <NotMeasured /> · xem <span className="num">cost/cost-estimate.md</span></span>
        <a className="btn btn--primary" href="#/dang-quet">Bắt đầu quét</a>
      </ActionBar>
    </div>
  );
}

const SCAN_STEPS = [
  { t: "Đọc schema và cấu hình", d: "scanner.py · không gọi AI", r: "2 bảng, 8 cột", ai: false },
  { t: "Tìm lời gọi ra ngoài và cách xin đồng ý", d: "scanner.py · không gọi AI", r: "1 lời gọi OpenAI, 2 dấu hiệu đồng ý sai", ai: false },
  { t: "AI phân loại tên cột", d: "classify.py · model nhỏ", r: "8 cột", ai: true },
  { t: "AI kiểm chứng đường đi dữ liệu", d: "verify.py · model lớn · xác nhận hoặc bác bỏ", r: "1 đường đi", ai: true },
  { t: "Rule engine ra kết luận", d: "rules.py · không gọi AI · nơi duy nhất tạo kết luận pháp lý", r: "C1, C2, C3", ai: false },
];

function ScreenDangQuet() {
  const { state, set } = useApp();
  const [step, setStep] = useState(0);
  useEffect(() => {
    setStep(0);
    const id = setInterval(() => setStep((s) => (s >= SCAN_STEPS.length ? s : s + 1)), 900);
    return () => clearInterval(id);
  }, [state.mode]);
  const done = step >= SCAN_STEPS.length;
  const rule = state.mode === "rule";

  const log = [
    ["static", "schema: 2 bảng / 8 cột"],
    ["static", "sink: openai.chat.completions.create · route.ts:10"],
    ["static", "consent: defaultChecked · page.tsx:5"],
    ["static", "consent: \"tiếp tục sử dụng\" · page.tsx:8"],
    rule ? ["skip", "llm-s phân loại cột: bỏ qua, chế độ rule"] : ["llm-s", "phân loại 8 cột · 1 lô"],
    rule ? ["skip", "llm-L kiểm chứng đường đi: bỏ qua, chế độ rule"] : ["llm-L", "đường 1/1 · users.email → chat.completions.create"],
    ["rule", "C1 KICH_HOAT · C2 KICH_HOAT_NANG · C3 " + c3Status(state.loaiHinh, state.luyKe)],
  ];
  const shown = log.slice(0, Math.min(log.length, step + 2));

  return (
    <div className="screen">
      <div className="wrap page">
        <div className="page-head">
          <div>
            <div className="meta"><span>{state.repo}</span><span>chế độ {state.mode}</span></div>
            <h1>{done ? "Quét xong. Năm bước, hai bước dùng AI." : "Đang quét repo…"}</h1>
          </div>
          <div className="seg" role="group" aria-label="Chế độ">
            {["rule", "hybrid"].map((m) => <button key={m} type="button" aria-pressed={state.mode === m} onClick={() => set({ mode: m })}>{m}</button>)}
          </div>
        </div>

        <div className="grid-2r" style={{ gap: 40 }}>
          <div className="stack" style={{ "--gap": "24px" }}>
            <ol className="timeline">
              {SCAN_STEPS.map((s, i) => {
                const skipped = rule && s.ai;
                const cls = i < step ? "done" : i === step ? "now" : "wait";
                return (
                  <li key={i} className={cls}>
                    <span className="dot">{i < step ? "✓" : i + 1}</span>
                    <div>
                      <h3>
                        {s.t}
                        {s.ai && <Chip kind={skipped ? "none" : "human"}>{skipped ? "bỏ qua" : "AI"}</Chip>}
                        {i === step && !done && <span className="chip chip--line pulse">đang chạy</span>}
                      </h3>
                      <p>{s.d}{i < step && !skipped ? " · " + s.r : ""}</p>
                    </div>
                  </li>
                );
              })}
            </ol>
            <div className="note note--cool">
              Bước 3 và 4 là hai việc duy nhất AI làm. Bước 5 chỉ nhận từ AI nhãn phân loại cột và cờ xác nhận đường đi; số điều, khoản, mức phạt đọc từ bảng luật JSON.
            </div>
          </div>

          <div className="night" style={{ padding: 22 }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 16 }}>
              <h2 style={{ fontSize: 20, letterSpacing: "-0.02em" }}>Nhật ký cổng AI</h2>
              <span className="xs muted">ghi vào <span className="num">traces/run-N.jsonl</span></span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>
              {[["Lượt gọi LLM", rule ? "0" : null], ["Token", rule ? "0" : null], ["Chi phí", rule ? "0" : null, "đ"]].map(([l, v, u]) => (
                <div key={l} className="stat">
                  <div className="label">{l}</div>
                  <div className="val">{v == null ? <NotMeasured night /> : <>{v} {u && <small>{u}</small>}</>}</div>
                </div>
              ))}
            </div>
            <div className="log" style={{ marginTop: 14, borderTop: "1px solid var(--color-night-rule)", minHeight: 260 }}>
              {shown.map(([k, t], i) => (
                <div key={i}>
                  <span className="t">{String(i * 7).padStart(2, "0")}s</span>
                  <span className={k === "skip" ? "skip" : k.startsWith("llm") ? "k-llm" : k === "rule" ? "k-rule" : "k-static"}>{k === "skip" ? "" : k + " "}</span>
                  <span className={k === "skip" ? "skip" : undefined}>{t}</span>
                </div>
              ))}
              {!done && <div className="pulse" style={{ color: "var(--color-night-muted)" }}>…</div>}
            </div>
            {!rule && <p className="xs muted" style={{ marginTop: 10 }}>Token và chi phí lấy từ <span className="num">usage</span> của API, chưa có lượt chạy hybrid nào cho repo này.</p>}
          </div>
        </div>
      </div>
      <ActionBar>
        <span className="small muted">Thời gian quét: <NotMeasured /></span>
        <a className={"btn " + (done ? "btn--primary" : "")} href="#/ket-qua" aria-disabled={!done}>Xem kết quả</a>
      </ActionBar>
    </div>
  );
}

function ScreenKetQua() {
  const { state } = useApp();
  const c3 = c3Status(state.loaiHinh, state.luyKe);
  const lh = SHP.loaiHinh.find(([v]) => v === state.loaiHinh)[1];
  const c3Codes = SHP.mienTru[state.loaiHinh] || [];
  return (
    <div className="screen">
      <div className="wrap page">
        <div className="page-head">
          <div>
            <div className="meta"><span>{state.repo}</span><span>chế độ {state.mode}</span><span>{lh.toLowerCase()}</span><span>đã gửi ra ngoài: {state.mode === "rule" ? "không gửi gì" : "tên cột + đoạn code đã lọc"}</span></div>
            <h1>Hai nghĩa vụ đã phát sinh{c3 === "CAN_NGUOI_XAC_NHAN" ? ", một điểm chờ bạn xác nhận." : ", và không còn miễn trừ."}</h1>
            <p className="lede">Đây là danh sách nghĩa vụ đã phát sinh, không phải kết luận vi phạm. Mỗi dòng có bằng chứng trong code và điều luật làm căn cứ.</p>
          </div>
        </div>

        <div className="note note--human row" style={{ marginBottom: 28, "--gap": "16px 28px", justifyContent: "space-between" }}>
          <div style={{ flex: "1 1 520px" }}>
            <h4>{c3 === "CAN_NGUOI_XAC_NHAN" ? "Không còn miễn trừ, nhưng cần bạn chốt loại hình" : "Không còn miễn trừ Điều 21, 22 và khoản 2 Điều 33"}</h4>
            Cột <span className="num">bookings.vi_tri_gan_nhat</span> là dữ liệu vị trí, nhóm nhạy cảm <span className="num">ND356 D4h</span>. Dù loại hình nào, kết luận đều là không còn miễn trừ; loại hình chỉ đổi căn cứ.
          </div>
          {c3 === "CAN_NGUOI_XAC_NHAN" && <a className="btn btn--primary btn--sm" href="#/quet">Chốt loại hình</a>}
        </div>

        <div className="bench">
          <div className="grid-3">
            <Entry c="c1" kind="C1 · Điều 20 Luật 91" where="route.ts:10" title="Chuyển dữ liệu cá nhân ra nước ngoài"
              cells={[["Trường", "users.email", { mono: true }], ["Đích", "chat.completions.create", { mono: true }],
                      ["Căn cứ", "Luat91 D20.1, D20.2", { mono: true }], ["Hạn", "60 ngày", { mono: true }],
                      ["Mức phạt tham khảo (khung, tổ chức)", "30–50 triệu đồng · ND330 D56.1", { wide: true }]]}
              foot={<><Status s="KICH_HOAT" /><a className="btn btn--sm" href="#/bang-chung/c1">Xem bằng chứng</a></>} />
            <Entry c="c2" kind="C2 · Điều 9 Luật 91" where="page.tsx:5, :8" title="Cách xin đồng ý không hợp lệ"
              cells={[["Dòng 5", "Ô đồng ý tích sẵn"], ["Dòng 8", "Im lặng là đồng ý"],
                      ["Căn cứ", "Luat91 D9.3, D9.4d", { mono: true }], ["Căn cứ", "ND356 D6, D6.3", { mono: true }],
                      ["Mức phạt tham khảo (khung, tổ chức)", "50–70 triệu đồng · ND330 D43.2b", { wide: true }]]}
              foot={<><Status s="KICH_HOAT_NANG" /><a className="btn btn--sm" href="#/bang-chung/c2">Xem bằng chứng</a></>} />
            <Entry c="c3" kind="C3 · Điều 38 Luật 91" where="001_init.sql:12" title="Miễn trừ cho doanh nghiệp nhỏ"
              cells={[["Nhóm", "vi_tri_dinh_vi", { mono: true }], ["Độ tin cậy", "1.0", { mono: true }],
                      ["Loại hình", lh], ["Căn cứ", c3Codes.length && c3 === "MAT_MIEN_TRU" ? c3Codes.join(", ") : "chờ chốt loại hình", { mono: !!c3Codes.length && c3 === "MAT_MIEN_TRU" }],
                      ["Cột", "bookings.vi_tri_gan_nhat", { mono: true, wide: true }]]}
              foot={<><Status s={c3} /><a className="btn btn--sm" href="#/phan-loai">Rà soát 8 cột</a></>} />
          </div>
        </div>

        <div className="grid-2" style={{ marginTop: 28 }}>
          <div className="note note--plain">
            <h4>Hệ thống từ chối kết luận khi thiếu căn cứ</h4>
            Repo này không có đường đi nào thiếu căn cứ. Khi dữ liệu gửi ra ngoài chỉ là chữ người dùng tự nhập, C1 chuyển sang <b>Cần luật sư rà soát</b> thay vì đoán. <a href="#/luat-su">Xem ví dụ trạng thái này</a>
          </div>
          <div className="note note--cool">
            <h4>Hồ sơ nháp chỉ sinh sau khi bạn duyệt</h4>
            Bạn xác nhận từng phát hiện ở cổng duyệt; phát hiện chưa xác nhận không vào hồ sơ.
          </div>
        </div>
      </div>
      <ActionBar>
        <span className="small muted">Kết quả là gợi ý từ phân tích tĩnh để người chịu trách nhiệm xác nhận, không phải ý kiến pháp lý.</span>
        <a className="btn btn--primary" href="#/duyet">Sang cổng duyệt</a>
      </ActionBar>
    </div>
  );
}

Object.assign(window, { ScreenQuet, ScreenDangQuet, ScreenKetQua });
