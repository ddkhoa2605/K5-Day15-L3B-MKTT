// Điều hướng bằng hash (#/ket-qua) và trạng thái dùng chung giữa các màn.

function parseRoute() {
  const [, route = "quet", arg] = (location.hash || "#/quet").split("/");
  return { route, arg };
}

const INITIAL = {
  repo: SHP.repo.path,
  loaiHinh: "khong_ro",
  luyKe: "khong_ro",
  mode: "rule",
  decisions: {},
  colDecisions: {},
  approved: { c1: true, c2: true, c3: true },
  reviewer: "",
  role: "",
  ack: false,
};

function App() {
  const [{ route, arg }, setRoute] = useState(parseRoute());
  const [state, setState] = useState(INITIAL);
  const set = (patch) => setState((s) => ({ ...s, ...patch }));

  useEffect(() => {
    const on = () => { setRoute(parseRoute()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);

  const screens = {
    "quet": <ScreenQuet />,
    "dang-quet": <ScreenDangQuet />,
    "ket-qua": <ScreenKetQua />,
    "bang-chung": <ScreenBangChung which={arg === "c2" ? "c2" : "c1"} />,
    "phan-loai": <ScreenPhanLoai />,
    "luat-su": <ScreenLuatSu />,
    "duyet": <ScreenDuyet />,
    "ho-so": <ScreenHoSo />,
    "logic": <ScreenLogic />,
    "ablation": <ScreenAblation />,
  };

  return (
    <AppCtx.Provider value={{ state, set }}>
      <TopBar route={route} />
      <main key={route + (arg || "")}>{screens[route] || screens.quet}</main>
    </AppCtx.Provider>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
