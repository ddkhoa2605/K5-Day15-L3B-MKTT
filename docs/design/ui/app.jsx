// Điều hướng bằng hash (#/ket-qua) và trạng thái dùng chung giữa các màn.
// Kết quả quét / phân tích / bản nháp lấy từ backend (api.js), lưu vào sessionStorage để tải lại trang không mất.

function parseRoute() {
  const [, route = "quet", arg] = (location.hash || "#/quet").split("/");
  return { route, arg };
}

const INITIAL = {
  // đầu vào
  nguon: "demo",          // demo | github | zip | case
  demoRepo: "",
  githubUrl: "",
  caseText: "",
  loaiHinh: "khong_ro",
  soChuThe: "",           // chuỗi số
  soKhongRo: true,        // người dùng chọn "Không rõ" số chủ thể
  mode: "rule",           // rule (không gọi model) | hybrid
  // từ backend
  scan: null,             // response POST /api/scan
  result: null,           // response analyze / business
  draft: null,            // response confirm
  // quyết định của người duyệt (chỉ ở FE, không gửi BE)
  decisions: {},
  colDecisions: {},
  approved: {},
  reviewer: "",
  role: "",
  ack: false,
};

const KEEP = ["nguon", "demoRepo", "githubUrl", "caseText", "loaiHinh", "soChuThe", "soKhongRo", "mode", "scan", "result", "draft",
              "decisions", "colDecisions", "approved", "reviewer", "role", "ack"];

function loadState() {
  try { return { ...INITIAL, ...JSON.parse(sessionStorage.getItem("shp_state") || "{}") }; }
  catch (e) { return INITIAL; }
}

function App() {
  const [{ route, arg }, setRoute] = useState(parseRoute());
  const [state, setState] = useState(loadState);
  const [be, setBe] = useState({ ok: null });
  const set = (patch) => setState((s) => ({ ...s, ...patch }));

  useEffect(() => {
    const on = () => { setRoute(parseRoute()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);

  useEffect(() => {
    const keep = {};
    KEEP.forEach((k) => { keep[k] = state[k]; });
    sessionStorage.setItem("shp_state", JSON.stringify(keep));
  }, [state]);

  useEffect(() => {
    API.health().then((h) => setBe({ ok: true, ...h })).catch((e) => setBe({ ok: false, err: e.message }));
  }, []);

  const screens = {
    "quet": <ScreenQuet />,
    "dang-quet": <ScreenDangQuet />,
    "ket-qua": <ScreenKetQua />,
    "bang-chung": <ScreenBangChung which={["c1", "c2", "c3"].includes(arg) ? arg : "c1"} />,
    "phan-loai": <ScreenPhanLoai />,
    "luat-su": <ScreenLuatSu />,
    "duyet": <ScreenDuyet />,
    "ho-so": <ScreenHoSo />,
    "logic": <ScreenLogic />,
    "ablation": <ScreenAblation />,
  };

  return (
    <AppCtx.Provider value={{ state, set, be }}>
      <TopBar route={route} be={be} />
      <main key={route + (arg || "")}>{screens[route] || screens.quet}</main>
    </AppCtx.Provider>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
