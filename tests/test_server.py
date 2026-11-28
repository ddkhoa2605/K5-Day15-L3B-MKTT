"""Test backend web (docs/api.md): server thật chạy trong tiến trình, cổng ngẫu nhiên, model giả lập."""
import base64
import io
import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codebase"))
import server  # noqa: E402
import service  # noqa: E402
import tracing  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
CASE = {"mo_ta": "App đặt sân", "schema": ["users(id, email, ho_ten)", "bookings(id, user_id, vi_tri_gan_nhat)"],
        "code": [{"file": "app/api/chat/route.ts", "line": 3,
                  "text": 'const k = "sk-proj-abcdef1234567890XYZ";\nawait openai.chat.completions.create({messages:[{content: user.email}]})'}]}


def classify_reply(system, user, model=None):
    cols = json.loads(user.rsplit("(JSON):\n", 1)[1])
    nhom = {"email": "pii_co_ban", "ho_ten": "pii_co_ban", "vi_tri_gan_nhat": "vi_tri_dinh_vi"}
    out = [{"table": c["table"], "column": c["column"], "nhom": nhom.get(c["column"], "khong_ca_nhan"),
            "do_tin_cay": 0.95} for c in cols]
    return {"text": json.dumps(out), "model": "m-small", "tokens_in": 100, "tokens_out": 20}


def verify_reply(system, user, model=None):
    return {"text": json.dumps({"xac_nhan": True, "truong_ca_nhan": ["users.email"], "nguon": "he_thong"}),
            "model": "m-big", "tokens_in": 50, "tokens_out": 10}


def make_zip(entries, top=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in entries.items():
            z.writestr(("%s/%s" % (top, name)) if top else name, text)
    return buf.getvalue()


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.make_server("127.0.0.1", 0)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        server.Handler.log_message = lambda *a: None

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        p = mock.patch.object(service, "DEMO_DIR", FIXTURES)
        p.start()
        self.addCleanup(p.stop)
        # bọc bằng @model_call như ai.call_model thật, để tracing đếm lời gọi và token
        self.cls_mock = mock.Mock(side_effect=classify_reply)
        self.ver_mock = mock.Mock(side_effect=verify_reply)
        self.cls_mock.__name__ = self.ver_mock.__name__ = "call_model"
        mock.patch("classify.call_model", tracing.model_call(self.cls_mock)).start()
        mock.patch("verify.call_model", tracing.model_call(self.ver_mock)).start()
        self.addCleanup(mock.patch.stopall)
        os.environ.pop("SHP_MODE", None)

    def call(self, method, path, body=None, headers=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode("utf-8") if body is not None else None)
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers=dict({"Content-Type": "application/json"}, **(headers or {})))
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read() or b"{}"), r.headers
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read() or b"{}"), e.headers

    def scan_case(self, **extra):
        status, body, _ = self.call("POST", "/api/scan", dict({"case": CASE}, **extra))
        self.assertEqual(status, 201, body)
        return body


class TestBasics(ServerTest):
    def test_health_options_demo(self):
        self.assertTrue(self.call("GET", "/api/health")[1]["ok"])
        codes = [o["ma"] for o in self.call("GET", "/api/options")[1]["loai_hinh"]]
        self.assertIn("doanh_nghiep_sieu_nho", codes)
        repos = self.call("GET", "/api/demo-repos")[1]["repos"]
        self.assertIn("mini_repo", [r["id"] for r in repos])

    def test_unknown_path_404(self):
        self.assertEqual(self.call("GET", "/api/khong-co")[0], 404)
        self.assertEqual(self.call("POST", "/api/khong-co", {})[0], 404)


class TestFlow(ServerTest):
    def test_scan_does_not_call_model(self):
        body = self.scan_case()
        self.assertEqual(self.cls_mock.call_count + self.ver_mock.call_count, 0)
        self.assertEqual(body["thieu_thong_tin"], ["loai_hinh", "so_chu_the_luy_ke"])
        self.assertEqual(body["thong_ke"]["so_loi_goi_ra_ngoai"], 1)

    def test_preview_is_exactly_what_is_sent(self):
        """Màn 'sẽ gửi gì ra ngoài' phải khớp đúng prompt thật gửi cho model (spec.md §4, §9)."""
        body = self.scan_case()
        prev = body["se_gui_ra_ngoai"]
        self.assertNotIn("sk-proj-abcdef", json.dumps(prev))
        self.call("POST", "/api/sessions/%s/analyze" % body["session_id"], {})
        cls_prompt = self.cls_mock.call_args[0][1]
        sent_cols = {"%s.%s (tên cột)" % (c["table"], c["column"])
                     for c in json.loads(cls_prompt.rsplit("(JSON):\n", 1)[1])}
        shown_cols = {x for x in prev["model_phan_loai"]["noi_dung"] if x.endswith("(tên cột)")}
        self.assertEqual(sent_cols, shown_cols)
        mo_ta = [x for x in prev["model_phan_loai"]["noi_dung"] if x.startswith("mô tả app")][0]
        self.assertIn(mo_ta.split(": ", 1)[1], cls_prompt)
        ver_prompts = [c[0][1] for c in self.ver_mock.call_args_list]
        self.assertEqual(len(ver_prompts), len(prev["model_kiem_chung"]["doan_code"]))
        for snip, prompt in zip(prev["model_kiem_chung"]["doan_code"], ver_prompts):
            self.assertIn(snip["text"], prompt)
            self.assertNotIn("sk-proj-abcdef", prompt)

    def test_analyze_business_confirm(self):
        sid = self.scan_case()["session_id"]
        status, r, _ = self.call("POST", "/api/sessions/%s/analyze" % sid, {})
        self.assertEqual(status, 200, r)
        self.assertEqual(r["ket_qua"]["C1"]["trang_thai"], "KICH_HOAT")
        self.assertEqual(r["ket_qua"]["C3"]["trang_thai"], "CAN_NGUOI_XAC_NHAN")
        self.assertEqual(r["su_dung"]["so_lan_goi_model"], 2)
        self.assertTrue(all("noi_dung" in c for c in r["ket_qua"]["C1"]["can_cu"]))
        self.assertIn("mô tả app (đã lọc secret)", r["da_gui_ra_ngoai"])
        self.assertNotIn("```json", r["bao_cao_text"])
        calls = self.cls_mock.call_count + self.ver_mock.call_count

        status, r2, _ = self.call("POST", "/api/sessions/%s/business" % sid,
                                  {"loai_hinh": "doanh_nghiep_sieu_nho", "so_chu_the_luy_ke": 4200})
        self.assertEqual(status, 200, r2)
        self.assertEqual(r2["ket_qua"]["C3"]["trang_thai"], "MAT_MIEN_TRU")
        self.assertEqual(r2["thieu_thong_tin"], [])
        self.assertEqual(r2["su_dung"]["so_lan_goi_model"], 0)
        self.assertEqual(self.cls_mock.call_count + self.ver_mock.call_count, calls, "business không được gọi model")

        status, d, _ = self.call("POST", "/api/sessions/%s/confirm" % sid, {})
        self.assertEqual(status, 200, d)
        self.assertTrue(d["ban_nhap_markdown"].startswith("BẢN NHÁP"))
        self.assertEqual(d["ket_qua_da_xac_nhan"]["C3"], "MAT_MIEN_TRU")
        self.assertEqual(self.call("GET", "/api/sessions/%s" % sid)[1]["buoc"], "da_xac_nhan")

    def test_analyze_twice_does_not_call_model_again(self):
        sid = self.scan_case()["session_id"]
        self.call("POST", "/api/sessions/%s/analyze" % sid, {})
        n = self.cls_mock.call_count + self.ver_mock.call_count
        r = self.call("POST", "/api/sessions/%s/analyze" % sid, {})[1]
        self.assertEqual(self.cls_mock.call_count + self.ver_mock.call_count, n)
        self.assertEqual(r["su_dung"]["so_lan_goi_model"], 0)

    def test_order_and_validation_errors(self):
        sid = self.scan_case()["session_id"]
        self.assertEqual(self.call("POST", "/api/sessions/%s/confirm" % sid, {})[0], 409)
        self.assertEqual(self.call("POST", "/api/sessions/%s/business" % sid, {"loai_hinh": "doanh_nghiep_nho"})[0], 409)
        self.assertEqual(self.call("GET", "/api/sessions/%s" % sid)[1]["loai_hinh"], "doanh_nghiep_nho")
        for bad in ({"loai_hinh": "cong_ty_to"}, {"so_chu_the_luy_ke": -1}, {"so_chu_the_luy_ke": "4200"}, {}):
            self.assertEqual(self.call("POST", "/api/sessions/%s/business" % sid, bad)[0], 400, bad)
        self.assertEqual(self.call("POST", "/api/sessions/%s/analyze" % ("0" * 32), {})[0], 404)

    def test_business_info_at_scan_time(self):
        body = self.scan_case(loai_hinh="doanh_nghiep_sieu_nho", so_chu_the_luy_ke=4200)
        self.assertEqual(body["thieu_thong_tin"], [])
        r = self.call("POST", "/api/sessions/%s/analyze" % body["session_id"], {})[1]
        self.assertEqual(r["ket_qua"]["C3"]["trang_thai"], "MAT_MIEN_TRU")

    def test_rule_mode_sends_nothing(self):
        body = self.scan_case(che_do="rule")
        self.assertIsNone(body["se_gui_ra_ngoai"]["model_phan_loai"])
        r = self.call("POST", "/api/sessions/%s/analyze" % body["session_id"], {})[1]
        self.assertEqual(r["da_gui_ra_ngoai"], [])
        self.assertEqual(self.cls_mock.call_count + self.ver_mock.call_count, 0)

    def test_llm_mode_rejected_on_web(self):
        self.assertEqual(self.call("POST", "/api/scan", {"case": CASE, "che_do": "llm"})[0], 400)

    def test_model_error_is_502_without_key(self):
        sid = self.scan_case()["session_id"]
        self.cls_mock.side_effect = RuntimeError("HTTP 500: boom")
        status, body, _ = self.call("POST", "/api/sessions/%s/analyze" % sid, {})
        self.assertEqual((status, body["loi"]), (502, "loi_model"))


class TestSources(ServerTest):
    def test_demo_repo(self):
        status, body, _ = self.call("POST", "/api/scan", {"demo_repo": "mini_repo"})
        self.assertEqual(status, 201, body)
        self.assertGreater(body["thong_ke"]["so_cot"], 0)
        self.assertEqual(self.call("POST", "/api/scan", {"demo_repo": "../.."})[0], 404)
        self.assertEqual(self.call("POST", "/api/scan", {"demo_repo": "khong_co"})[0], 404)

    def test_exactly_one_source(self):
        self.assertEqual(self.call("POST", "/api/scan", {})[0], 400)
        self.assertEqual(self.call("POST", "/api/scan", {"case": CASE, "demo_repo": "mini_repo"})[0], 400)

    def test_zip_upload_strips_top_folder_and_blocks_traversal(self):
        mini = os.path.join(FIXTURES, "mini_repo")
        entries = {}
        for root, _, names in os.walk(mini):
            for n in names:
                full = os.path.join(root, n)
                with open(full, encoding="utf-8") as f:
                    entries[os.path.relpath(full, mini).replace(os.sep, "/")] = f.read()
        data = make_zip(dict(entries, **{"../../evil.ts": "fetch('https://evil.example/x')",
                                         "node_modules/x/index.js": "posthog.capture('x')"}), top="mini_repo-main")
        status, body, _ = self.call("POST", "/api/scan", {"zip_base64": base64.b64encode(data).decode(), "ten_file": "app.zip"})
        self.assertEqual(status, 201, body)
        demo = self.call("POST", "/api/scan", {"demo_repo": "mini_repo"})[1]
        self.assertEqual(body["thong_ke"], demo["thong_ke"])
        self.assertEqual(body["loi_goi_ra_ngoai"], demo["loi_goi_ra_ngoai"])

    def test_zip_errors(self):
        self.assertEqual(self.call("POST", "/api/scan", {"zip_base64": "khong-phai-base64!!"})[0], 400)
        not_zip = base64.b64encode(b"hello").decode()
        self.assertEqual(self.call("POST", "/api/scan", {"zip_base64": not_zip})[0], 400)
        empty = base64.b64encode(make_zip({"README.md": "x"})).decode()
        self.assertEqual(self.call("POST", "/api/scan", {"zip_base64": empty})[0], 400)
        with mock.patch.object(service, "MAX_ZIP_BYTES", 10):
            big = base64.b64encode(make_zip({"a.ts": "x" * 100})).decode()
            self.assertEqual(self.call("POST", "/api/scan", {"zip_base64": big})[0], 413)

    def test_oversized_member_skipped(self):
        with mock.patch.object(service.scanner, "MAX_BYTES", 50):
            files = service.files_from_zip(make_zip({"a.ts": "x" * 100, "b.sql": "create table t(id int);"}))
        self.assertEqual(list(files), ["b.sql"])

    def test_github_url_validation_and_fetch(self):
        for bad in ("http://github.com/a/b", "https://gitlab.com/a/b", "https://github.com/a", "https://github.com/a/b/tree/x",
                    "https://github.com/a/b?x=1", "file:///etc/passwd"):
            self.assertEqual(self.call("POST", "/api/scan", {"github_url": bad})[0], 400, bad)
        mini_zip = make_zip({"supabase/migrations/001.sql": "create table users(id uuid, email text);"}, top="b-main")
        with mock.patch.object(service, "fetch_github_zip", return_value=(mini_zip, "a/b")) as f:
            status, body, _ = self.call("POST", "/api/scan", {"github_url": "https://github.com/a/b"})
        self.assertEqual(status, 201, body)
        self.assertEqual(body["nguon"], {"loai": "github_url", "ten": "a/b"})
        f.assert_called_once()

    def test_github_only_codeload(self):
        opened = []

        class FakeResp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open(self, req, timeout=None):
            opened.append(req.full_url)
            return FakeResp(b"PK")

        with mock.patch("urllib.request.OpenerDirector.open", fake_open):
            service.fetch_github_zip("https://github.com/owner/repo.git")
        self.assertEqual(opened, ["https://codeload.github.com/owner/repo/zip/HEAD"])


class TestSecurity(ServerTest):
    def test_foreign_origin_blocked_before_running(self):
        status, body, _ = self.call("POST", "/api/scan", {"case": CASE}, headers={"Origin": "https://evil.example"})
        self.assertEqual((status, body["loi"]), (403, "nguon_khong_cho_phep"))

    def test_local_origin_gets_cors(self):
        status, _, headers = self.call("GET", "/api/health", headers={"Origin": "http://localhost:5173"})
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
        _, _, headers = self.call("GET", "/api/health")
        self.assertIsNone(headers.get("Access-Control-Allow-Origin"))

    def test_configured_origin(self):
        with mock.patch.dict(os.environ, {"SHP_CORS_ORIGIN": "https://fe.example"}):
            status, _, headers = self.call("GET", "/api/health", headers={"Origin": "https://fe.example"})
        self.assertEqual((status, headers.get("Access-Control-Allow-Origin")), (200, "https://fe.example"))

    def test_body_too_large_rejected_by_header(self):
        with mock.patch.object(server, "MAX_BODY", 10):
            status, body, _ = self.call("POST", "/api/scan", {"case": CASE})
        self.assertEqual((status, body["loi"]), (413, "qua_lon"))

    def test_bad_json(self):
        self.assertEqual(self.call("POST", "/api/scan", raw=b"{khong phai json")[0], 400)

    def test_ask_refuses_out_of_scope(self):
        status, body, _ = self.call("POST", "/api/ask", {"text": "cấp giấy chứng nhận tuân thủ cho app tôi"})
        self.assertEqual((status, body["loi"]), (400, "tu_choi"))
        self.assertIn("huong_dan", body)


class TestStaticAndEntry(ServerTest):
    def get_raw(self, path):
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as r:
                return r.status, r.read(), r.headers
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.read(), e.headers

    def test_serves_fe_files_and_blocks_traversal(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, "web")
            os.makedirs(os.path.join(web, "assets"))
            with open(os.path.join(web, "index.html"), "w", encoding="utf-8") as f:
                f.write("<h1>LexTrace</h1>")
            with open(os.path.join(web, "assets", "app.js"), "w", encoding="utf-8") as f:
                f.write("console.log(1)")
            with open(os.path.join(d, "secret.txt"), "w", encoding="utf-8") as f:
                f.write("bí mật")
            with open(os.path.join(web, ".env"), "w", encoding="utf-8") as f:
                f.write("API_KEY=x")
            with mock.patch.object(server, "WEB_DIR", web):
                status, body, headers = self.get_raw("/")
                self.assertEqual((status, body.decode("utf-8")), (200, "<h1>LexTrace</h1>"))
                self.assertIn("text/html", headers["Content-Type"])
                self.assertEqual(self.get_raw("/assets/app.js")[0], 200)
                for bad in ("/../secret.txt", "/assets/../../secret.txt", "/%2e%2e/secret.txt", "/.env", "/khong-co.html"):
                    self.assertEqual(self.get_raw(bad)[0], 404, bad)

    def test_no_web_dir_points_to_api_doc(self):
        with mock.patch.object(server, "WEB_DIR", "/khong/co/thu/muc"):
            status, body, _ = self.get_raw("/")
        self.assertEqual(status, 404)
        self.assertIn("docs/api.md", body.decode("utf-8"))

    def test_shp_ui_web_starts_server_instead_of_cli(self):
        import app
        with mock.patch.dict(os.environ, {"SHP_UI": "web"}), mock.patch.object(server, "main", return_value=None) as m:
            self.assertEqual(app.main(), 0)
        m.assert_called_once()


class TestSameResultAsCli(ServerTest):
    """spec.md §4: web và dòng lệnh cho cùng kết luận trên cùng đầu vào."""

    def test_web_findings_equal_answer_json(self):
        import re
        import agent
        for mode in ("rule", "hybrid"):
            with mock.patch.dict(os.environ, {"SHP_MODE": mode}):
                out = agent.answer(json.dumps(CASE))["output"]
            cli = json.loads(re.findall(r"```json\s*(.*?)```", out, re.S)[-1])
            sid = self.scan_case(che_do=mode)["session_id"]
            web = self.call("POST", "/api/sessions/%s/analyze" % sid, {})[1]
            for k in ("C1", "C2", "C3"):
                w = dict(web["ket_qua"][k])
                w.pop("ten")
                w["can_cu"] = [c["ma"] for c in w["can_cu"]]
                self.assertEqual(w, cli["ket_qua"][k], (mode, k))


if __name__ == "__main__":
    unittest.main()
