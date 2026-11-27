// Dữ liệu cho bản thiết kế. Lấy từ output thật:
//   SHP_MODE=rule python -c "import agent; agent.answer('repo:tests/fixtures/mini_repo')"
// và từ data/legal/*.json, codebase/rules.py, eval/metric_spec.yaml.
// Số nào chưa đo thì để null và giao diện hiện "(chưa đo)". Không điền số tự nghĩ ra.

window.SHP = {
  repo: {
    path: "repo:tests/fixtures/mini_repo",
    name: "mini_repo",
    tables: 2,
    columns: 8,
  },

  loaiHinh: [
    ["khong_ro", "Chưa rõ"],
    ["ho_kinh_doanh", "Hộ kinh doanh"],
    ["doanh_nghiep_sieu_nho", "Doanh nghiệp siêu nhỏ"],
    ["doanh_nghiep_nho", "Doanh nghiệp nhỏ"],
    ["khoi_nghiep", "Doanh nghiệp khởi nghiệp"],
    ["doanh_nghiep_lon", "Doanh nghiệp lớn"],
  ],

  // exemption.json
  mienTru: {
    nguong: 100000,
    ho_kinh_doanh: ["Luat91 D38.3", "ND356 D41.2"],
    doanh_nghiep_sieu_nho: ["Luat91 D38.3", "ND356 D41.2"],
    doanh_nghiep_nho: ["Luat91 D38.2", "ND356 D41.1"],
    khoi_nghiep: ["Luat91 D38.2", "ND356 D41.1"],
  },

  files: {
    route: { path: "app/api/chat/route.ts", start: 7, lines: [
      '  const { msg, userId } = await req.json();',
      '  const supabase = createClient(process.env.SUPABASE_URL!, [đã lọc]);',
      '  const { data: user } = await supabase.from("Users").select("email")',
      '  const r = await openai.chat.completions.create({',
      '    model: "gpt-4o-mini",',
      '    messages: [{ role: "user", content: user.email + ": " + msg }],',
      '  });',
    ]},
    signup: { path: "app/signup/page.tsx", start: 3, lines: [
      '    <form>',
      '      <label>',
      '        <input type="checkbox" defaultChecked />',
      '        Tôi đồng ý với điều khoản sử dụng',
      '      </label>',
      '      <p>Bằng việc tiếp tục sử dụng, bạn được coi là đồng ý với chính sách.</p>',
      '    </form>',
    ]},
    sql: { path: "supabase/migrations/001_init.sql", start: 2, lines: [
      'create table if not exists public."Users" (',
      '  id uuid primary key default gen_random_uuid(),',
      '  email text unique not null,',
      '  "Ho_Ten" text,',
      '  created_at timestamptz default now()',
      ');',
      '',
      'create table bookings (',
      '  id uuid primary key,',
      '  user_id uuid references public."Users"(id) on delete cascade,',
      '  vi_tri_gan_nhat text,',
      '  gia numeric(10, 2),',
    ]},
  },

  // citations.json (rút gọn phần sau dấu gạch)
  cite: {
    "Luat91 D20.1": "Các trường hợp chuyển dữ liệu cá nhân xuyên biên giới, gồm cả việc dùng nền tảng ngoài lãnh thổ Việt Nam để xử lý dữ liệu thu thập tại Việt Nam (điểm c).",
    "Luat91 D20.2": "Phải lập hồ sơ đánh giá tác động chuyển dữ liệu xuyên biên giới và gửi 01 bản chính cho cơ quan chuyên trách trong 60 ngày kể từ ngày đầu tiên chuyển.",
    "Luat91 D20.6": "Các trường hợp không phải đánh giá tác động chuyển dữ liệu xuyên biên giới, gồm cả việc chủ thể dữ liệu tự chuyển dữ liệu của mình (điểm c).",
    "Luat91 D9.3": "Sự đồng ý phải rõ ràng, cụ thể, có thể in, sao chép bằng văn bản, kể cả dạng điện tử hoặc định dạng kiểm chứng được.",
    "Luat91 D9.4d": "Sự im lặng hoặc không phản hồi không được coi là sự đồng ý.",
    "ND356 D6": "Phương thức xin đồng ý phải kiểm chứng được: ai đồng ý, lúc nào, đồng ý gì; bên kiểm soát lưu và chứng minh khi có tranh chấp.",
    "ND356 D6.3": "Không được thiết lập phương thức mặc định đồng ý, hoặc chỉ dẫn gây hiểu lầm giữa đồng ý và không đồng ý.",
    "ND356 D4h": "Vị trí của cá nhân được xác định qua dịch vụ định vị.",
    "Luat91 D38.2": "Doanh nghiệp nhỏ, khởi nghiệp được chọn thực hiện hay không Điều 21, 22, khoản 2 Điều 33 trong 05 năm kể từ ngày Luật có hiệu lực, trừ ba trường hợp loại trừ.",
    "Luat91 D38.3": "Hộ kinh doanh, doanh nghiệp siêu nhỏ không phải thực hiện Điều 21, 22, khoản 2 Điều 33, trừ ba trường hợp loại trừ.",
    "ND356 D41.1": "Doanh nghiệp nhỏ, khởi nghiệp: được lựa chọn, trừ ba trường hợp loại trừ.",
    "ND356 D41.2": "Hộ kinh doanh, doanh nghiệp siêu nhỏ: không phải thực hiện, trừ ba trường hợp loại trừ (ngưỡng 100 nghìn chủ thể tích lũy).",
  },

  // classify.classify_rule trên 8 cột của fixture
  columns: [
    { col: "bookings.vi_tri_gan_nhat", line: 12, nhom: "vi_tri_dinh_vi", conf: 1.0 },
    { col: "users.email", line: 4, nhom: "pii_co_ban", conf: 1.0 },
    { col: "users.ho_ten", line: 5, nhom: "pii_co_ban", conf: 1.0 },
    { col: "users.id", line: 3, nhom: "khong_ca_nhan", conf: 0.5 },
    { col: "users.created_at", line: 6, nhom: "khong_ca_nhan", conf: 0.5 },
    { col: "bookings.id", line: 10, nhom: "khong_ca_nhan", conf: 0.5 },
    { col: "bookings.user_id", line: 11, nhom: "khong_ca_nhan", conf: 0.5 },
    { col: "bookings.gia", line: 13, nhom: "khong_ca_nhan", conf: 0.5 },
  ],

  // sensitive_categories.json (Điều 4 NĐ 356)
  nhom: {
    chung_toc_dan_toc: ["a", "Nguồn gốc chủng tộc, dân tộc"],
    chinh_tri_ton_giao: ["b", "Quan điểm chính trị, tôn giáo, tín ngưỡng"],
    doi_tu_rieng_tu: ["c", "Đời sống riêng tư, bí mật cá nhân, gia đình"],
    suc_khoe: ["d", "Tình trạng sức khỏe"],
    sinh_trac_di_truyen: ["đ", "Sinh trắc học, đặc điểm di truyền"],
    tinh_duc: ["e", "Đời sống, xu hướng tình dục"],
    toi_pham: ["g", "Tội phạm, vi phạm pháp luật do cơ quan thực thi thu thập"],
    vi_tri_dinh_vi: ["h", "Vị trí xác định qua dịch vụ định vị"],
    dinh_danh_dien_tu: ["i", "Tài khoản định danh điện tử, ảnh thẻ căn cước"],
    tai_chinh: ["k", "Tài khoản ngân hàng, thẻ, giao dịch, tín dụng, bảo hiểm"],
    hanh_vi_mang: ["l", "Theo dõi hành vi trên không gian mạng"],
  },

  // eval/metric_spec.yaml — chuẩn "đạt" chốt ở CP2
  metrics: [
    { name: "phan_loai_viet_tat", label: "Phân loại đúng tên cột viết tắt tiếng Việt", why: "chứng minh AI cần thiết", threshold: "≥ 85% câu tag=vt" },
    { name: "trich_dan_dung", label: "Trích dẫn đúng số điều, số khoản", why: "chứng minh rule engine cần thiết", threshold: "100% câu kích hoạt" },
    { name: "bao_dong_gia", label: "Báo động giả trên câu âm tính", why: "", threshold: "≤ 10% câu tag=am" },
    { name: "tu_choi_dung", label: "Từ chối đúng khi thiếu căn cứ", why: "", threshold: "≥ 90% câu nhóm này" },
  ],
  benchmarkSize: 20,
  casesSize: 60,

  // chưa đo: điền khi có eval/run-N.csv, traces/run-N.jsonl, cost/simulate-N.csv
  measured: {
    tokens: null, costVnd: null, llmCalls: null, scanSeconds: null, manualMinutes: null,
    ablation: null, // { phan_loai_viet_tat: {A, B, C}, ... }
  },
};
